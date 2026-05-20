"""
Audio inference wrapper.

Routing logic (updated after Priority 3 ESC-50 regression):
  - If preprocessing flags `non_speech`, we do NOT reject the audio.
    Instead we return an "inconclusive" result: P(fake) = 0.5 with
    availability = True but a strong `non_speech` quality flag.
    The fusion engine will see very low audio reliability (r_a near 0
    because score is exactly 0.5) and will effectively fall back to
    video-only, without marking audio as unavailable.
  - If preprocessing flags hard quality issues (too_short, too_quiet),
    we still mark audio unavailable — these genuinely cannot be analysed.
  - Normal speech follows the existing CNN path.

This replaces the previous "reject all non-speech" design, which caused
either too many "No usable audio" errors (strict) or fake-audio false
negatives (relaxed).
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from models.model_loader import get_model_for
from preprocessing.audio_preprocessor import logmel_to_tensor

log = logging.getLogger("deeptection.inference.audio")


def infer_audio(preproc: Dict[str, Any], source: str | None = None
                ) -> Dict[str, Any]:
    out = {
        "available": False,
        "score": None,
        "duration_sec": (preproc or {}).get("duration_sec", 0.0),
        "quality": (preproc or {}).get("quality", {}) or {},
        "model": None,
        "unavailable_reason": None,
    }

    # ---- Hard failures: file couldn't be read, too short, or silent ----
    if not preproc or not preproc.get("ok"):
        out["unavailable_reason"] = (
            (preproc or {}).get("error") or "Audio could not be processed."
        )
        return out

    quality = preproc.get("quality") or {}

    # Genuinely unusable — can't analyse at all
    if quality.get("too_short"):
        out["unavailable_reason"] = (
            "Audio is too short for reliable analysis."
        )
        return out
    if quality.get("too_quiet"):
        out["unavailable_reason"] = (
            "Audio is too quiet — the signal is nearly silent."
        )
        return out

    # ---- Soft failure: non-speech content ----
    # The model was trained only on speech (ASVspoof + codec-compressed
    # speech). It is unsafe to trust its output on music, environmental
    # noise, or non-vocal audio. Instead of rejecting, we return a
    # *neutral* score (0.5) so fusion can downweight us and fall back
    # to video.
    if quality.get("non_speech"):
        out["available"] = True
        out["score"] = 0.5                    # maximally uninformative
        out["model"] = "audio:non_speech_gated"
        log.info("Audio gated as non-speech (reason=%s); returning neutral score.",
                 quality.get("non_speech_reason", "unknown"))
        return out

    # ---- Normal path: speech present, run the CNN ----
    bundle = get_model_for("audio", source)
    try:
        if bundle.kind == "hf_audio":
            score = float(bundle.predict(preproc["waveform"]))
        else:
            tensor = logmel_to_tensor(preproc["logmel"])
            score = float(bundle.predict(tensor))
    except Exception as exc:  # noqa: BLE001
        log.exception("Audio inference failed: %s", exc)
        out["unavailable_reason"] = f"Audio model error: {exc.__class__.__name__}"
        return out

    score = max(0.0, min(1.0, score))

    out["available"] = True
    out["score"] = round(score, 4)
    out["model"] = bundle.name
    return out