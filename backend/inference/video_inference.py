"""
Video inference wrapper with optional two-model ensemble.

Local model = stronger fake detector
HF model    = stronger real-video checker

The ensemble reduces false positives when local says fake but HF says real.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import numpy as np
import torch
from PIL import Image

import config
from models.model_loader import get_model_for, get_video_model_pair


log = logging.getLogger("deeptection.inference.video")


def _tensor_to_pil_list(frames: torch.Tensor):
    """Convert (N, 3, H, W) in [0,1] → list of PIL.Image."""
    np_frames = (
        frames.permute(0, 2, 3, 1)
        .cpu()
        .numpy()
        * 255.0
    ).clip(0, 255).astype(np.uint8)

    return [Image.fromarray(f) for f in np_frames]


def _score_with_bundle(bundle, frames: torch.Tensor, pil_list) -> float:
    """Run correct input type depending on model backend."""
    if bundle.kind == "hf_image":
        return float(bundle.predict(pil_list))
    return float(bundle.predict(frames))


def _combine_video_scores(local_score: float, hf_score: float):
    real_t = config.ENSEMBLE_REAL_THRESHOLD
    fake_t = config.ENSEMBLE_FAKE_THRESHOLD

    if local_score <= real_t and hf_score <= real_t:
        return min(local_score, hf_score), "consensus_real"

    if local_score >= fake_t and hf_score >= fake_t:
        return max(local_score, hf_score), "consensus_fake"

    if local_score >= fake_t and hf_score <= real_t:
        return (local_score + hf_score) / 2.0, "disagreement_local_fake"

    if local_score <= real_t and hf_score >= fake_t:
        return hf_score, "disagreement_hf_fake"

    return (local_score + hf_score) / 2.0, "ambiguous"


def infer_video(preproc: Dict[str, Any], source: str | None = None) -> Dict[str, Any]:
    out = {
        "available": False,
        "score": None,
        "num_frames": 0,
        "quality": preproc.get("quality", {}) if preproc else {},
        "model": None,
        "ensemble": None,
        "unavailable_reason": None,
    }

    if not preproc or not preproc.get("ok"):
        out["unavailable_reason"] = (
            (preproc or {}).get("error") or "Video could not be processed."
        )
        return out

    frames: torch.Tensor = preproc["frames"]
    if frames is None or frames.shape[0] == 0:
        out["unavailable_reason"] = "No usable frames extracted."
        return out

    try:
        pil_list = _tensor_to_pil_list(frames)

        use_ensemble = (
            getattr(config, "VIDEO_ENSEMBLE", False)
            and source not in ("local", "hf")
        )

        if use_ensemble:
            local_bundle, hf_bundle = get_video_model_pair()

            local_score = _score_with_bundle(local_bundle, frames, pil_list)
            hf_score = _score_with_bundle(hf_bundle, frames, pil_list)

            combined_score, mode = _combine_video_scores(local_score, hf_score)
            score = max(0.0, min(1.0, combined_score))

            out["model"] = f"Ensemble({local_bundle.name} + {hf_bundle.name})"
            out["ensemble"] = {
                "mode": mode,
                "local_score": round(local_score, 4),
                "hf_score": round(hf_score, 4),
                "combined": round(score, 4),
            }

            log.info(
                "Video ensemble: local=%.3f hf=%.3f combined=%.3f mode=%s",
                local_score,
                hf_score,
                score,
                mode,
            )

        else:
            bundle = get_model_for("video", source)
            raw_score = _score_with_bundle(bundle, frames, pil_list)
            score = max(0.0, min(1.0, raw_score))
            out["model"] = bundle.name

    except Exception as exc:
        log.exception("Video inference failed: %s", exc)
        out["unavailable_reason"] = f"Video model error: {exc.__class__.__name__}"
        return out

    out["available"] = True
    out["score"] = round(score, 4)
    out["num_frames"] = int(frames.shape[0])
    return out