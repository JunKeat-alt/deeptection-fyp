"""
Lightweight file-backed history store. Thread-safe via a module-level lock.

Chose JSON over SQLite because:
 - FYP demo doesn't need queries
 - JSON is trivial to inspect for screenshots
 - Fewer dependencies for Hugging Face Spaces deployment
"""

import json
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List

import config


_LOCK = threading.Lock()


def _load() -> List[Dict[str, Any]]:
    if not config.LOG_FILE.exists():
        return []
    try:
        with config.LOG_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _save(entries: List[Dict[str, Any]]) -> None:
    with config.LOG_FILE.open("w", encoding="utf-8") as fh:
        json.dump(entries, fh, ensure_ascii=False, indent=2)


def add_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a new history entry at the top. Returns the stored entry."""
    entry = {
        "id": entry.get("id") or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **entry,
    }
    with _LOCK:
        entries = _load()
        entries.insert(0, entry)
        if len(entries) > config.HISTORY_MAX_ENTRIES:
            entries = entries[: config.HISTORY_MAX_ENTRIES]
        _save(entries)
    return entry


def list_entries(limit: int = 50) -> List[Dict[str, Any]]:
    with _LOCK:
        entries = _load()
    return entries[: max(0, int(limit))]


def clear_entries() -> int:
    with _LOCK:
        entries = _load()
        n = len(entries)
        _save([])
    return n
