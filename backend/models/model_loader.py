"""
Model loader — local-first strategy with optional HuggingFace path.

Selection policy (see config.MODEL_SOURCE):
    "auto"  → local checkpoint → HF → untrained local (warn-only safety net)
    "local" → local checkpoint only, error if missing
    "hf"    → HuggingFace only, error if unreachable

Every returned ModelBundle exposes the same .predict interface so the
inference layer is agnostic to which backend is active.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import numpy as np
import torch
import torch.nn.functional as F

import config
from .audio_model import load_local_audio_model
from .video_model import load_local_video_model

log = logging.getLogger("deeptection.models")


# --------------------------------------------------------------------------- #
#                            Bundle + caches                                  #
# --------------------------------------------------------------------------- #
@dataclass
class ModelBundle:
    name: str                      # Human-readable identifier shown in UI/logs
    kind: str                      # "hf_image" | "hf_audio" | "local_image" | "local_audio"
    predict: Callable[..., float]  # Returns P(fake) ∈ [0, 1]
    meta: Dict[str, Any]


_video_bundle: Optional[ModelBundle] = None
_audio_bundle: Optional[ModelBundle] = None
_load_lock = threading.Lock()


# ========================================================================== #
#                              VIDEO — HF PATH                                #
# ========================================================================== #
def _build_hf_video_bundle() -> ModelBundle:
    from transformers import AutoImageProcessor, AutoModelForImageClassification

    model_id = config.VIDEO_MODEL_HF
    log.info("Loading HuggingFace video model: %s", model_id)

    processor = AutoImageProcessor.from_pretrained(
        model_id, cache_dir=str(config.STORAGE_DIR)
    )
    model = AutoModelForImageClassification.from_pretrained(
        model_id, cache_dir=str(config.STORAGE_DIR)
    ).to(config.DEVICE).eval()

    id2label = {int(k): str(v).lower() for k, v in model.config.id2label.items()}
    fake_indices = [i for i, lbl in id2label.items()
                    if any(t in lbl for t in ("fake", "deepfake", "synthetic", "spoof"))]
    if not fake_indices:
        fake_indices = [max(id2label.keys())]

    @torch.inference_mode()
    def predict(pil_images) -> float:
        inputs = processor(images=pil_images, return_tensors="pt").to(config.DEVICE)
        logits = model(**inputs).logits
        probs = F.softmax(logits, dim=-1)
        return float(probs[:, fake_indices].sum(dim=-1).mean().item())

    return ModelBundle(
        name=f"HF:{model_id}",
        kind="hf_image",
        predict=predict,
        meta={"id2label": id2label, "fake_indices": fake_indices},
    )


# ========================================================================== #
#                          VIDEO — LOCAL (TRAINED) PATH                       #
# ========================================================================== #
def _build_local_video_bundle(require_trained: bool) -> ModelBundle:
    """
    Local MobileNetV3-Small. Loads fine-tuned weights from
    config.VIDEO_CHECKPOINT_PATH if present.

    require_trained=True  → raise FileNotFoundError if the checkpoint is missing.
                            Used by "local" mode for reproducibility guarantees.
    require_trained=False → fall through to untrained backbone (auto-mode safety net).
    """
    ckpt = config.VIDEO_CHECKPOINT_PATH
    trained = False
    state_error: Optional[str] = None

    model = load_local_video_model(device=config.DEVICE)

    if ckpt.is_file():
        try:
            state = torch.load(str(ckpt), map_location=config.DEVICE)
            model.load_state_dict(state)
            model.eval()
            trained = True
            log.info("Loaded fine-tuned video checkpoint: %s (%.1f KB)",
                     ckpt, ckpt.stat().st_size / 1024)
        except Exception as exc:  # noqa: BLE001
            state_error = str(exc)
            log.error("Video checkpoint at %s failed to load: %s", ckpt, exc)
    else:
        log.warning("No video checkpoint at %s.", ckpt)

    if require_trained and not trained:
        raise FileNotFoundError(
            f"MODEL_SOURCE='local' requires a valid video checkpoint at "
            f"{ckpt}. " + (f"Load error: {state_error}" if state_error else
                           "File does not exist.")
        )

    @torch.inference_mode()
    def predict(frames_tensor: torch.Tensor) -> float:
        """frames_tensor: (N, 3, H, W) in [0, 1]  → mean P(fake)."""
        logits = model(frames_tensor.to(config.DEVICE))
        probs = F.softmax(logits, dim=-1)
        return float(probs[:, 1].mean().item())

    status = "fine-tuned" if trained else "untrained"
    return ModelBundle(
        name=f"Local:MobileNetV3-Small ({status})",
        kind="local_image",
        predict=predict,
        meta={"trained": trained,
              "checkpoint": str(ckpt) if trained else None,
              "load_error": state_error},
    )


# ========================================================================== #
#                              AUDIO — HF PATH                                #
# ========================================================================== #
def _build_hf_audio_bundle() -> ModelBundle:
    from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

    model_id = config.AUDIO_MODEL_HF
    log.info("Loading HuggingFace audio model: %s", model_id)

    extractor = AutoFeatureExtractor.from_pretrained(
        model_id, cache_dir=str(config.STORAGE_DIR)
    )
    model = AutoModelForAudioClassification.from_pretrained(
        model_id, cache_dir=str(config.STORAGE_DIR)
    ).to(config.DEVICE).eval()

    id2label = {int(k): str(v).lower() for k, v in model.config.id2label.items()}
    fake_indices = [i for i, lbl in id2label.items()
                    if any(t in lbl for t in ("fake", "spoof", "synthetic", "deepfake"))]
    if not fake_indices:
        fake_indices = [max(id2label.keys())]

    sr = getattr(extractor, "sampling_rate", config.AUDIO_TARGET_SR)

    @torch.inference_mode()
    def predict(waveform: np.ndarray) -> float:
        inputs = extractor(waveform, sampling_rate=sr, return_tensors="pt")
        inputs = {k: v.to(config.DEVICE) for k, v in inputs.items()}
        logits = model(**inputs).logits
        probs = F.softmax(logits, dim=-1)
        return float(probs[:, fake_indices].sum(dim=-1).mean().item())

    return ModelBundle(
        name=f"HF:{model_id}",
        kind="hf_audio",
        predict=predict,
        meta={"id2label": id2label, "fake_indices": fake_indices,
              "sampling_rate": sr},
    )


# ========================================================================== #
#                         AUDIO — LOCAL (TRAINED) PATH                        #
# ========================================================================== #
def _build_local_audio_bundle(require_trained: bool) -> ModelBundle:
    ckpt = config.AUDIO_CHECKPOINT_PATH
    trained = False
    state_error: Optional[str] = None

    model = load_local_audio_model(device=config.DEVICE)

    if ckpt.is_file():
        try:
            state = torch.load(str(ckpt), map_location=config.DEVICE)
            model.load_state_dict(state)
            model.eval()
            trained = True
            log.info("Loaded fine-tuned audio checkpoint: %s (%.1f KB)",
                     ckpt, ckpt.stat().st_size / 1024)
        except Exception as exc:  # noqa: BLE001
            state_error = str(exc)
            log.error("Audio checkpoint at %s failed to load: %s", ckpt, exc)
    else:
        log.warning("No audio checkpoint at %s.", ckpt)

    if require_trained and not trained:
        raise FileNotFoundError(
            f"MODEL_SOURCE='local' requires a valid audio checkpoint at "
            f"{ckpt}. " + (f"Load error: {state_error}" if state_error else
                           "File does not exist.")
        )

    from .audio_model import MelCNN  # noqa: F401 — kept for type checks

    @torch.inference_mode()
    def predict(logmel_tensor: torch.Tensor) -> float:
        """logmel_tensor: (1, 1, n_mels, T)  → P(fake)."""
        logits = model(logmel_tensor.to(config.DEVICE))
        probs = F.softmax(logits, dim=-1)
        return float(probs[0, 1].item())

    status = "fine-tuned" if trained else "untrained"
    return ModelBundle(
        name=f"Local:MelCNN ({status})",
        kind="local_audio",
        predict=predict,
        meta={"trained": trained,
              "checkpoint": str(ckpt) if trained else None,
              "load_error": state_error},
    )


# ========================================================================== #
#                       PUBLIC: video / audio selection                       #
# ========================================================================== #
def _select_video_bundle() -> ModelBundle:
    source = config.MODEL_SOURCE

    if source == "local":
        log.info("MODEL_SOURCE=local → loading fine-tuned video model (strict).")
        return _build_local_video_bundle(require_trained=True)

    if source == "hf":
        log.info("MODEL_SOURCE=hf → loading HuggingFace video model (strict).")
        return _build_hf_video_bundle()

    # auto
    log.info("MODEL_SOURCE=auto → trying local video checkpoint first.")
    if config.VIDEO_CHECKPOINT_PATH.is_file():
        try:
            return _build_local_video_bundle(require_trained=True)
        except Exception as exc:  # noqa: BLE001
            log.warning("Local video checkpoint exists but failed to load "
                        "(%s). Trying HuggingFace.", exc)

    try:
        return _build_hf_video_bundle()
    except Exception as exc:  # noqa: BLE001
        log.warning("HuggingFace video model unavailable (%s). "
                    "Falling back to untrained local architecture.", exc)

    return _build_local_video_bundle(require_trained=False)


def _select_audio_bundle() -> ModelBundle:
    source = config.MODEL_SOURCE

    if source == "local":
        log.info("MODEL_SOURCE=local → loading fine-tuned audio model (strict).")
        return _build_local_audio_bundle(require_trained=True)

    if source == "hf":
        log.info("MODEL_SOURCE=hf → loading HuggingFace audio model (strict).")
        return _build_hf_audio_bundle()

    # auto
    log.info("MODEL_SOURCE=auto → trying local audio checkpoint first.")
    if config.AUDIO_CHECKPOINT_PATH.is_file():
        try:
            return _build_local_audio_bundle(require_trained=True)
        except Exception as exc:  # noqa: BLE001
            log.warning("Local audio checkpoint exists but failed to load "
                        "(%s). Trying HuggingFace.", exc)

    try:
        return _build_hf_audio_bundle()
    except Exception as exc:  # noqa: BLE001
        log.warning("HuggingFace audio model unavailable (%s). "
                    "Falling back to untrained local architecture.", exc)

    return _build_local_audio_bundle(require_trained=False)


def get_video_model() -> ModelBundle:
    global _video_bundle
    with _load_lock:
        if _video_bundle is None:
            _video_bundle = _select_video_bundle()
        return _video_bundle


'''def get_audio_model() -> ModelBundle:
    global _audio_bundle
    with _load_lock:
        if _audio_bundle is None:
            _audio_bundle = _select_audio_bundle()
        return _audio_bundle
        '''
def get_audio_model():
    return get_model_for("audio", "hf")
    
# --------------------------------------------------------------------------- #
#         Per-source caches (for UI-driven switching between backends)        #
# --------------------------------------------------------------------------- #
# We cache one bundle per (modality, source). They're lazily built on first
# request so startup isn't slowed down by loading a model nobody might use.

_bundle_cache: Dict[str, ModelBundle] = {}  # key = f"{modality}:{source}"


def _build_for_source(modality: str, source: str) -> ModelBundle:
    """Build a bundle for a specific modality/source, bypassing MODEL_SOURCE."""
    if modality == "video":
        if source == "hf":
            return _build_hf_video_bundle()
        # "local"
        return _build_local_video_bundle(require_trained=True)
    else:  # audio
        if source == "hf":
            return _build_hf_audio_bundle()
        return _build_local_audio_bundle(require_trained=True)


def get_model_for(modality: str, source: Optional[str] = None) -> ModelBundle:
    """
    Return a bundle for the requested (modality, source) pair.

    modality: "video" or "audio"
    source:   "local" | "hf" | None (None → falls back to MODEL_SOURCE policy)

    Thread-safe, cached per-source. First call for a given source is slow
    (model download / checkpoint load); subsequent calls are free.
    """
    # No explicit per-request source → use the global policy path
    if source is None:
        return get_video_model() if modality == "video" else get_audio_model()

    source = source.strip().lower()
    if source not in ("local", "hf"):
        raise ValueError(f"source must be 'local' or 'hf', got {source!r}")
    if modality not in ("video", "audio"):
        raise ValueError(f"modality must be 'video' or 'audio', got {modality!r}")

    key = f"{modality}:{source}"
    with _load_lock:
        if key in _bundle_cache:
            return _bundle_cache[key]
        log.info("Building on-demand bundle for %s", key)
        bundle = _build_for_source(modality, source)
        _bundle_cache[key] = bundle
        return bundle
    

def get_video_model_pair() -> tuple[ModelBundle, ModelBundle]:
    """
    Return both local fine-tuned and Hugging Face video bundles.
    Used by video ensemble inference.
    """
    local_bundle = get_model_for("video", "local")
    hf_bundle = get_model_for("video", "hf")
    return local_bundle, hf_bundle


# ========================================================================== #
#                              Warm-up helper                                 #
# ========================================================================== #
def warm_up_models() -> None:
    """Pre-load both models so the first /analyze request isn't slow."""
    log.info("Warming up models (MODEL_SOURCE=%s)…", config.MODEL_SOURCE)
    v = get_video_model()
    a = get_audio_model()
    log.info("Video model ready: %s", v.name)
    log.info("Audio model ready: %s", a.name)