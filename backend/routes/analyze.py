"""
/api/analyze — main endpoint.

Accepts a multipart upload with field name "file".
Pipeline:
    validate → save → preprocess (video and/or audio) →
    infer (parallel modalities) → fuse → explain → log → respond.

Response shape (on success):
{
  "ok": true,
  "id": "...",
  "media_type": "video" | "audio",
  "filename": "...",
  "duration_sec": 12.4,
  "verdict": "real" | "fake" | "uncertain",
  "final_score": 0.73,
  "confidence": 0.82,
  "video":  { "available": ..., "score": ..., "model": ..., "num_frames": ..., "quality": {...} },
  "audio":  { "available": ..., "score": ..., "model": ..., "quality": {...} },
  "fusion": { "used_modalities": [...], "fallback_note": "..."|null },
  "explanation": { "simple": "...", "details": [{"modality": "...", "reasons": [...]}], ... },
  "timings_ms": { "preprocess": ..., "infer": ..., "total": ... }
}
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any, Tuple
from utils.analysis_id import generate_analysis_id

from flask import Blueprint, jsonify, request
from utils.decision_log import log_decision

import config
from inference.audio_inference import infer_audio
from inference.fusion import fuse_and_decide
from inference.video_inference import infer_video
from preprocessing.audio_preprocessor import preprocess_audio
from preprocessing.video_preprocessor import (
    extract_audio_from_video,
    preprocess_video,
)
from utils.explanation import build_explanation
from utils.file_utils import cleanup, save_upload, validate_upload
from utils.history_store import add_entry

bp = Blueprint("analyze", __name__)
log = logging.getLogger("deeptection.route.analyze")


def _process_video_with_audio(video_path, tmp_audio_path,
                              video_source=None, audio_source=None) -> Tuple[Dict[str, Any], Dict[str, Any], float]:
    """Run video preprocessing, then (if ffmpeg available) audio.
       Both preprocessors run, then both inferences run in parallel."""

    t0 = time.time()
    v_pre = preprocess_video(video_path)
    audio_extracted = extract_audio_from_video(video_path, tmp_audio_path)
    if audio_extracted:
        a_pre = preprocess_audio(tmp_audio_path)
    else:
        a_pre = {
            "ok": False,
            "error": "Video has no audio track or ffmpeg is unavailable on the server.",
            "quality": {}, "duration_sec": 0.0,
        }
    preproc_ms = (time.time() - t0) * 1000.0

    # Parallel inference
    t1 = time.time()
    with ThreadPoolExecutor(max_workers=2) as ex:
        fut_v = ex.submit(infer_video, v_pre, video_source)
        fut_a = ex.submit(infer_audio, a_pre, audio_source)
        v_res = fut_v.result()
        a_res = fut_a.result()
    infer_ms = (time.time() - t1) * 1000.0

    return v_res, a_res, preproc_ms + infer_ms


def _process_audio_only(path, audio_source=None) -> Tuple[Dict[str, Any], Dict[str, Any], float]:
    t0 = time.time()
    a_pre = preprocess_audio(path)
    a_res = infer_audio(a_pre, audio_source)
    v_res = {
        "available": False,
        "score": None,
        "num_frames": 0,
        "quality": {},
        "model": None,
        "unavailable_reason": "No video was uploaded.",
    }
    elapsed = (time.time() - t0) * 1000.0
    return v_res, a_res, elapsed


@bp.route("/analyze", methods=["POST"])
def analyze():
    total_t = time.time()
    analysis_id = generate_analysis_id() # ← generate once, use in any response path

    if "file" not in request.files:
        return jsonify({
            "ok": False,
            "error": "missing_file",
            "message": 'Please attach your media file in the "file" field.',
        }), 400

    upload = request.files["file"]
    ok, media_type, err = validate_upload(upload)
    if not ok:
        return jsonify({"ok": False, "error": "invalid_file", "message": err}), 400

    lang = (request.form.get("lang") or "en").strip().lower()
    if lang not in ("en", "en_simple"):
        lang = "en"

    # ---- Read analysis mode ----
    mode = (request.form.get("mode") or config.DEFAULT_ANALYSIS_MODE).strip().lower()

    if mode not in config.ANALYSIS_MODES:
        mode = config.DEFAULT_ANALYSIS_MODE

    mode_config = config.ANALYSIS_MODES[mode]

    audio_source = mode_config["audio_source"]
    video_source = mode_config["video_source"]   # None = ensemble
    

    saved_path = save_upload(upload, media_type)
    tmp_audio: Path | None = None

    try:
        if media_type == "video":
            tmp_audio = saved_path.with_suffix(".tmp.wav")
            v_res, a_res, _ = _process_video_with_audio(
                saved_path,
                tmp_audio,
                video_source=video_source,
                audio_source=audio_source,
            )
        else:  # audio-only upload
            v_res, a_res, _ = _process_audio_only(
                saved_path,
                audio_source=audio_source,
            )

        # ----- Quality gate (Priority 5) -----
        v_usable = (
            bool(v_res.get("available"))
            and not _is_video_unusable(v_res.get("quality") or {})
        )
        a_usable = (
            bool(a_res.get("available"))
            and not _is_audio_unusable(a_res.get("quality") or {})
        )

        if not v_usable and not a_usable:
            total_ms = (time.time() - total_t) * 1000.0
            rejected = {
                "ok": True,
                "id": analysis_id,
                "media_type": media_type,
                "filename": upload.filename,
                "verdict": "uncertain",
                "final_score": 0.5,
                "confidence": 0.0,
                "video": v_res,
                "audio": a_res,
                "fusion": {
                    "used_modalities": [],
                    "fallback_note": (
                        "The file quality is too low for reliable deepfake analysis. "
                        "Please try a clearer recording."
                    ),
                    "video_weight": None,
                    "audio_weight": None,
                    "mode": "rejected_low_quality",
                },
                "explanation": {
                    "simple_key": "result.simple.uncertain",
                    "verdict": "uncertain",
                    "final_score": 0.5,
                    "confidence": 0.0,
                    "details": [{
                        "modality": "system",
                        "reason_keys": ["reason.system.low_quality"],
                    }],
                },
                "timings_ms": {"total": round(total_ms, 1)},
                "model_source": source or config.MODEL_SOURCE,
            }
            return jsonify(rejected)
        # ----- end gate -----

        fusion = fuse_and_decide(v_res, a_res)

        explanation = build_explanation(
            verdict=fusion["verdict"],
            final_score=fusion["final_score"],
            confidence=fusion["confidence"],
            video=v_res,
            audio=a_res,
            lang=lang,
        )

        duration = (a_res.get("duration_sec") or 0.0)
        if v_res.get("available"):
            # prefer video duration if we have it
            # (frame count is known but duration comes from preproc meta — approximate)
            pass

        total_ms = (time.time() - total_t) * 1000.0


        result = {
            "ok": True,
            "mode": mode,
            "mode_label": mode_config["label"],
            "id": analysis_id, # ← NEW
            "media_type": media_type,
            "filename": upload.filename,
            "verdict": fusion["verdict"],
            "final_score": fusion["final_score"],
            "confidence": fusion["confidence"],
            "video": v_res,
            "audio": a_res,
            "fusion": {
                "used_modalities": fusion["used_modalities"],
                "fallback_note": fusion["fallback_note"],
                "video_weight": fusion["video_weight"],   # NEW — dynamic reliability
                "audio_weight": fusion["audio_weight"],   # NEW — dynamic reliability
                "mode": fusion["fusion_mode"],            # NEW — "weighted" / "override_fake" / etc.
            },
            "explanation": explanation,
            "timings_ms": {"total": round(total_ms, 1)},
        }

        # ---- Log to history ----
        history_entry = add_entry({
            "id": analysis_id,
            "filename": upload.filename,
            "media_type": media_type,
            "verdict": fusion["verdict"],
            "final_score": fusion["final_score"],
            "confidence": fusion["confidence"],
            "video_score": fusion["video_score"],
            "audio_score": fusion["audio_score"],
            "used_modalities": fusion["used_modalities"],
            "simple_explanation": explanation.get("simple_key", f"result.simple.{fusion['verdict']}"),
            "duration_ms": round(total_ms, 1),
        })
        result["id"] = history_entry["id"]
        result["timestamp"] = history_entry["timestamp"]

        try:
            log_decision(
                analysis_id=analysis_id,
                mode=mode,
                filename=upload.filename or "",
                video=v_res, audio=a_res, fusion=fusion,
            )
        except Exception:
            pass   # logging must never break the API response

        return jsonify(result)

    except Exception as exc:  # noqa: BLE001
        log.exception("Analyze failed: %s", exc)
        return jsonify({
            "ok": False,
            "error": "pipeline_error",
            "message": "An error occurred while analysing this file.",
        }), 500

    finally:
        # Cleanup temp files — keep uploads dir tidy
        cleanup(saved_path)
        if tmp_audio:
            cleanup(tmp_audio)

def _is_video_unusable(quality: dict) -> bool:
    if not quality:
        return False
    if quality.get("few_frames"):
        return True
    if quality.get("low_face_confidence") and quality.get("too_blurry"):
        return True
    return False


def _is_audio_unusable(quality: dict) -> bool:
    if not quality:
        return False
    if quality.get("too_quiet"):
        return True
    if quality.get("too_short"):
        return True
    if quality.get("non_speech"):
        return True
    return False
