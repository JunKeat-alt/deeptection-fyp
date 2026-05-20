"""
Explanation generator — language-neutral, key-based output.

The backend no longer embeds any user-facing English text. Instead, it
returns stable translation keys like "result.simple.real" or
"reason.audio.too_quiet". The frontend's i18n layer maps each key to
text in the user's selected language (English, Tamil, or Arabic).

This keeps the API surface language-agnostic: the same JSON response
works for every locale the frontend supports today and any locale it
adds in the future.
"""

from __future__ import annotations

from typing import Any, Dict, List


# ---- Simple verdict keys -------------------------------------------------- #
_VERDICT_SIMPLE_KEY: Dict[str, str] = {
    "real": "result.simple.real",
    "fake": "result.simple.fake",
    "uncertain": "result.simple.uncertain",
}


# ---- Per-modality reason selection --------------------------------------- #
def _video_reason_keys(video: Dict[str, Any]) -> List[str]:
    keys: List[str] = []
    if not video or not video.get("available"):
        return keys

    score = float(video.get("score", 0.0) or 0.0)
    quality = video.get("quality") or {}

        # NEW: video uncertain zone (important for fusion explanation)
    if 0.30 < score < 0.70:
        keys.append("reason.video.uncertain_signal")

    if score >= 0.75:
        keys.append("reason.video.strong_artefacts")
        
    elif score >= 0.60:
        keys.append("reason.video.minor_artefacts")

    if quality.get("low_face_confidence"):
        keys.append("reason.video.low_face_confidence")
    if quality.get("too_blurry"):
        keys.append("reason.video.too_blurry")
    if quality.get("few_frames"):
        keys.append("reason.video.few_frames")

    if score < 0.40 and not keys:
        keys.append("reason.video.natural")

    return keys


def _audio_reason_keys(audio: Dict[str, Any]) -> List[str]:
    keys: List[str] = []
    if not audio or not audio.get("available"):
        return keys

    score = float(audio.get("score", 0.0) or 0.0)
    quality = audio.get("quality") or {}

    if score >= 0.75:
        keys.append("reason.audio.strong_synthetic")
    elif score >= 0.60:
        keys.append("reason.audio.atypical")

    if quality.get("too_quiet"):
        keys.append("reason.audio.too_quiet")
    if quality.get("too_short"):
        keys.append("reason.audio.too_short")
    if quality.get("noisy"):
        keys.append("reason.audio.noisy")

    if score < 0.40 and not keys:
        keys.append("reason.audio.natural")

    return keys


# ---- Public entry point -------------------------------------------------- #
def build_explanation(
    verdict: str,
    final_score: float,
    confidence: float,
    video: Dict[str, Any],
    audio: Dict[str, Any],
    lang: str = "en",   # kept for backward compatibility; ignored
) -> Dict[str, Any]:
    """
    Assemble a language-neutral explanation payload.

    Output shape:
    {
      "simple_key":  "result.simple.real" | "result.simple.fake" | ...,
      "verdict":     "real" | "fake" | "uncertain",
      "final_score": float,
      "confidence":  float,
      "details": [
          {
              "modality": "video" | "audio" | "system",
              "reason_keys": ["reason.video.too_blurry", ...]
          },
          ...
      ]
    }
    """
    verdict = verdict if verdict in _VERDICT_SIMPLE_KEY else "uncertain"

    details: List[Dict[str, Any]] = []

    v_keys = _video_reason_keys(video)
    if v_keys:
        details.append({"modality": "video", "reason_keys": v_keys})
    elif video and not video.get("available"):
        details.append({
            "modality": "video",
            "reason_keys": ["reason.video.unavailable"],
        })

    a_keys = _audio_reason_keys(audio)
    if a_keys:
        details.append({"modality": "audio", "reason_keys": a_keys})
    elif audio and not audio.get("available"):
        details.append({
            "modality": "audio",
            "reason_keys": ["reason.audio.unavailable"],
        })

    # Modality-conflict note — fires only when both modalities are present
    # and produced conflicting scores.
    if (video and video.get("available")) and (audio and audio.get("available")):
        try:
            gap = abs(
                float(video.get("score", 0.0) or 0.0)
                - float(audio.get("score", 0.0) or 0.0)
            )
        except (TypeError, ValueError):
            gap = 0.0
        if gap >= 0.35:
            details.append({
                "modality": "system",
                "reason_keys": ["reason.system.conflict"],
            })

    if not details:
        details.append({
            "modality": "system",
            "reason_keys": ["reason.system.generic"],
        })

    return {
        "simple_key":  _VERDICT_SIMPLE_KEY[verdict],
        "verdict":     verdict,
        "final_score": round(float(final_score), 3),
        "confidence":  round(float(confidence), 3),
        "details":     details,
    }