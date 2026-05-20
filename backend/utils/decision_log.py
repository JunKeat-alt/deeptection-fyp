"""
Structured per-decision logger.

Writes one JSON line per analysis to backend/storage/decision_log.jsonl.
Used for offline pattern analysis when investigating failure modes.

This is INTENTIONALLY a separate stream from the Flask logger.
The Flask log is for operations; this is for ML behavior analysis.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import config

LOG_PATH = config.STORAGE_DIR / "decision_log.jsonl"
_lock = threading.Lock()


def log_decision(*, analysis_id: str, mode: str, filename: str,
                 video: Dict[str, Any], audio: Dict[str, Any],
                 fusion: Dict[str, Any]) -> None:
    """Append one decision record to the structured log."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "id": analysis_id,
        "mode": mode,
        "filename": filename,
        # Video summary
        "v_avail": video.get("available"),
        "v_score": video.get("score"),
        "v_ensemble_local": (video.get("ensemble") or {}).get("local_score"),
        "v_ensemble_hf":    (video.get("ensemble") or {}).get("hf_score"),
        "v_ensemble_mode":  (video.get("ensemble") or {}).get("mode"),
        "v_quality_flags":  list((video.get("quality") or {}).keys()),
        # Audio summary
        "a_avail": audio.get("available"),
        "a_score": audio.get("score"),
        "a_quality_flags": list((audio.get("quality") or {}).keys()),
        # Final
        "verdict": fusion.get("verdict"),
        "final_score": fusion.get("final_score"),
        "confidence": fusion.get("confidence"),
        "fusion_mode": fusion.get("fusion_mode"),
    }
    line = json.dumps(record, separators=(",", ":")) + "\n"
    with _lock:
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(line)