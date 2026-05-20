"""
Confidence-aware weighted fusion + decision engine (v2).

New in v2:
  1. Per-modality calibration offsets compensate for systematic bias
     observed in evaluation (video over-predicts fake; audio is
     over-confident out-of-distribution).
  2. Symmetric override rules — strong fake AND strong real can both
     override the weighted average, preventing one model from dragging
     the other when it is clearly out of distribution.
  3. Per-modality strong-evidence thresholds replace a single global one,
     so the noisier audio pathway needs a higher bar to override.
"""

from __future__ import annotations

from typing import Any, Dict

import config


# --------------------------------------------------------------------------- #
#                           Calibration + helpers                             #
# --------------------------------------------------------------------------- #
def _calibrate(raw: float, offset: float) -> float:
    """Shift raw P(fake) by an offset, clamped to [0, 1]."""
    if not config.CALIBRATION_ENABLED:
        return raw
    return max(0.0, min(1.0, raw - offset))


def _score_distance(score: float) -> float:
    return abs(score - 0.5) * 2.0


def _quality_penalty(quality: Dict[str, Any] | None) -> float:
    if not quality:
        return 0.0
    flag_weights = {
        "low_face_confidence": 0.15,
        "too_blurry":          0.15,
        "few_frames":          0.10,
        "too_quiet":           0.20,
        "too_short":           0.10,
        "noisy":               0.10,
    }
    return sum(w for f, w in flag_weights.items() if quality.get(f))


def _reliability(score: float, quality: Dict[str, Any] | None, modality: str = "audio") -> float:
    base_distance = _score_distance(score)
    penalty = _quality_penalty(quality)

    if modality == "video":
        if 0.30 < score < 0.70:
            base_distance *= 0.6

    return max(0.05, base_distance - penalty)


# --------------------------------------------------------------------------- #
#                        Main fusion + decision function                      #
# --------------------------------------------------------------------------- #
def fuse_and_decide(video: Dict[str, Any], audio: Dict[str, Any]
                    ) -> Dict[str, Any]:
    v_ok = bool(video and video.get("available"))
    a_ok = bool(audio and audio.get("available"))

    # -------- Calibrated scores --------
    s_v_raw = float(video["score"]) if v_ok else None
    s_a_raw = float(audio["score"]) if a_ok else None
    s_v = _calibrate(s_v_raw, config.VIDEO_SCORE_OFFSET) if v_ok else None
    s_a = _calibrate(s_a_raw, config.AUDIO_SCORE_OFFSET) if a_ok else None

    # -------- Case: neither modality --------
    if not v_ok and not a_ok:
        return _empty_result()

    # -------- Case: single modality --------
    if v_ok and not a_ok:
        r_v = _reliability(s_v, video.get("quality"), modality="video")
        return _package(
            final_score=s_v, confidence=max(0.0, r_v - 0.15),
            raw_v=s_v_raw, raw_a=None, cal_v=s_v, cal_a=None,
            w_v=1.0, w_a=None,
            mode="single_video",
            used=["video"],
            note="Audio unavailable — result is based on video only.",
        )
    if a_ok and not v_ok:
        r_a = _reliability(s_a, audio.get("quality"), modality="audio")
        return _package(
            final_score=s_a, confidence=max(0.0, r_a - 0.15),
            raw_v=None, raw_a=s_a_raw, cal_v=None, cal_a=s_a,
            w_v=None, w_a=1.0,
            mode="single_audio",
            used=["audio"],
            note="Video unavailable — result is based on audio only.",
        )

    # ----------------- Case 3: both modalities available ------------------
    r_v = _reliability(s_v, video.get("quality"), modality="video")
    r_a = _reliability(s_a, audio.get("quality"), modality="audio")

    # ---- Strong-evidence detection ----
    v_says_fake_strong = (s_v >= config.STRONG_FAKE_VIDEO and r_v >= 0.50)


    # ----audio says very strong but confirm the quality first ----
    audio_quality = audio.get("quality") or {}

    audio_override_allowed = not (
        audio_quality.get("too_quiet")
        or audio_quality.get("too_short")
        or audio_quality.get("noisy")
        or audio_quality.get("non_speech")
    )

    a_says_fake_strong = (
        s_a >= config.STRONG_FAKE_AUDIO
        and r_a >= 0.75
        and audio_override_allowed
    )


    
    v_says_real_strong = (s_v <= config.STRONG_REAL_VIDEO and r_v >= 0.50)
    a_says_real_strong = (s_a <= config.STRONG_REAL_AUDIO and r_a >= 0.50)

    # ------------------------------------------------------------------ #
    # AUDIO fake override — ONLY WHEN AUDIO QUALITY IS RELIABLE.
    # This protects against voice-clone attacks, but avoids false fake results
    # when audio is too quiet, too short, noisy, or non-speech.
    # ------------------------------------------------------------------ #
    if a_says_fake_strong:
        final_score = s_a
        confidence = max(0.70, min(1.0, 0.3 + r_a))
        return _package(
            final_score=final_score, confidence=confidence,
            raw_v=s_v_raw, raw_a=s_a_raw, cal_v=s_v, cal_a=s_a,
            w_v=r_v, w_a=r_a,
            mode="override_fake_audio",
            used=["video", "audio"],
            note="Strong evidence of manipulation in the audio. The final verdict follows the audio signal.",
            verdict_override="fake",
        )

    # ------------------------------------------------------------------ #
    # VIDEO fake override — VETOABLE BY STRONG-REAL AUDIO.
    # The video model is known to produce false positives on real-world
    # compressed footage (training distribution gap with OpenForensics).
    # Therefore a confident video-fake signal can be vetoed when the
    # more reliable audio modality strongly contradicts it.
    # ------------------------------------------------------------------ #
    if v_says_fake_strong:
        # Veto condition: audio is strongly real AND reliable enough to be trusted.
        audio_vetoes = (
            s_a <= config.STRONG_REAL_AUDIO   # e.g. 0.15
            and r_a >= 0.60                   # audio reliability must be high
        )
        if not audio_vetoes:
            final_score = s_v
            confidence = max(0.70, min(1.0, 0.3 + r_v))
            return _package(
                final_score=final_score, confidence=confidence,
                raw_v=s_v_raw, raw_a=s_a_raw, cal_v=s_v, cal_a=s_a,
                w_v=r_v, w_a=r_a,
                mode="override_fake_video",
                used=["video", "audio"],
                note="Strong evidence of manipulation in the video — "
                     "the final verdict follows that signal.",
                verdict_override="fake",
            )
        # else: fall through to weighted fusion below — audio's strong-real
        # signal will dominate the weighted average and produce verdict=real.

    # --------------------------------------------------------------------- #
    # RULE 2 — REAL OVERRIDE (REQUIRES BOTH MODALITIES TO AGREE)
    # Both modalities must be strongly real. A single real signal is
    # never enough to override. This protects against voice-clone attacks.
    # --------------------------------------------------------------------- #
    if v_says_real_strong and a_says_real_strong:
        final_score = (s_v + s_a) / 2.0
        avg_reliab = (r_v + r_a) / 2.0
        confidence = max(0.70, min(1.0, 0.3 + avg_reliab))
        return _package(
            final_score=final_score,
            confidence=confidence,
            raw_v=s_v_raw, raw_a=s_a_raw, cal_v=s_v, cal_a=s_a,
            w_v=r_v, w_a=r_a,
            mode="override_real",
            used=["video", "audio"],
            note="Both modalities clearly indicate the content is genuine.",
            verdict_override="real",
        )

    # RULE — STRONG REAL AUDIO + WEAK/AMBIGUOUS VIDEO
    # If audio is very confidently real and video is not strongly fake,
    # treat the final result as real instead of uncertain.
    if a_says_real_strong and not v_says_fake_strong and s_v < config.DECISION_FAKE_THRESHOLD:
        final_score = min(s_v, s_a)
        confidence = max(0.65, min(0.85, 0.25 + r_a))

        return _package(
            final_score=final_score,
            confidence=confidence,
            raw_v=s_v_raw, raw_a=s_a_raw, cal_v=s_v, cal_a=s_a,
            w_v=r_v, w_a=r_a,
            mode="audio_real_video_weak",
            used=["video", "audio"],
            note="The audio is strongly authentic and the video does not show strong fake evidence.",
            verdict_override="real",
        )

    # --------------------------------------------------------------------- #
    # RULE 3 — WEIGHTED FUSION (only reached when no override fires)
    # Now we're in the ambiguous zone. Use confidence-weighted average
    # and apply the standard confidence gate.
    # --------------------------------------------------------------------- #
    weighted_score = (r_v * s_v + r_a * s_a) / (r_v + r_a)

    raw_conf   = _score_distance(weighted_score)
    avg_reliab = (r_v + r_a) / 2.0
    agreement  = 1.0 - abs(s_v - s_a)
    confidence = 0.5 * raw_conf + 0.3 * avg_reliab + 0.2 * agreement

    # Conflict-cap rule applies ONLY here, in the weighted path —
    # it can no longer contradict a fake/real override, because those
    # already returned above.
    note = None
    verdict_override = None
    if abs(s_v - s_a) >= config.DECISION_MODALITY_CONFLICT:
        confidence = min(confidence, 0.45)
        verdict_override = "uncertain"
        note = (
            f"The video suggests {_label(s_v)} and the audio suggests "
            f"{_label(s_a)} — this disagreement reduces our confidence."
        )

    confidence = max(0.0, min(1.0, confidence))


    return _package(
        final_score=weighted_score,
        confidence=confidence,
        raw_v=s_v_raw, raw_a=s_a_raw, cal_v=s_v, cal_a=s_a,
        w_v=r_v, w_a=r_a,
        mode="weighted",
        used=["video", "audio"],
        note=note,
        verdict_override=verdict_override,
    )


# --------------------------------------------------------------------------- #
#                               Packaging                                     #
# --------------------------------------------------------------------------- #
def _label(score: float) -> str:
    if score >= config.DECISION_FAKE_THRESHOLD: return "fake"
    if score <= config.DECISION_REAL_THRESHOLD: return "real"
    return "uncertain"


def _decide_verdict(final_score: float, confidence: float) -> str:
    if confidence < config.DECISION_CONFIDENCE_MIN: return "uncertain"
    if final_score >= config.DECISION_FAKE_THRESHOLD: return "fake"
    if final_score <= config.DECISION_REAL_THRESHOLD: return "real"
    return "uncertain"


def _empty_result() -> Dict[str, Any]:
    return {
        "verdict": "uncertain", "final_score": 0.5, "confidence": 0.0,
        "video_score": None, "audio_score": None,
        "video_score_raw": None, "audio_score_raw": None,
        "video_weight": None, "audio_weight": None,
        "fusion_mode": "no_signal", "used_modalities": [],
        "fallback_note": "We could not analyse the file. Please try a different file.",
    }


def _package(*, final_score, confidence, raw_v, raw_a, cal_v, cal_a,
             w_v, w_a, mode, used, note, verdict_override=None):
    final_score = max(0.0, min(1.0, float(final_score)))
    confidence = max(0.0, min(1.0, float(confidence)))

    if verdict_override is not None:
        verdict = verdict_override
    else:
        verdict = _decide_verdict(final_score, confidence)

    return {
        "verdict": verdict,
        "final_score": round(final_score, 4),
        "confidence": round(confidence, 4),
        "video_score": round(cal_v, 4) if cal_v is not None else None,
        "audio_score": round(cal_a, 4) if cal_a is not None else None,
        "video_score_raw": round(raw_v, 4) if raw_v is not None else None,
        "audio_score_raw": round(raw_a, 4) if raw_a is not None else None,
        "video_weight": round(float(w_v), 4) if w_v is not None else None,
        "audio_weight": round(float(w_a), 4) if w_a is not None else None,
        "fusion_mode": mode,
        "used_modalities": used,
        "fallback_note": note,
    }