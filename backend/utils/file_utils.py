"""
File utilities: validation, safe saving, type detection.
"""

import mimetypes
import os
import uuid
from pathlib import Path
from typing import Tuple

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

import config


def get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def classify_media(filename: str) -> str:
    """Return 'video', 'audio' or 'unknown' based on extension."""
    ext = get_extension(filename)
    if ext in config.ALLOWED_VIDEO_EXTENSIONS:
        return "video"
    if ext in config.ALLOWED_AUDIO_EXTENSIONS:
        return "audio"
    return "unknown"


def validate_upload(file: FileStorage) -> Tuple[bool, str, str]:
    """
    Returns (ok, media_type, error_message).
    media_type ∈ {'video', 'audio'} if ok, else ''.
    """
    if file is None or not file.filename:
        return False, "", "No file provided."

    media_type = classify_media(file.filename)
    if media_type == "unknown":
        allowed = sorted(config.ALLOWED_VIDEO_EXTENSIONS | config.ALLOWED_AUDIO_EXTENSIONS)
        return False, "", (
            f"Unsupported file type. Allowed: {', '.join(allowed)}."
        )

    # Size check via seek/tell (Werkzeug gives a stream)
    file.stream.seek(0, os.SEEK_END)
    size_bytes = file.stream.tell()
    file.stream.seek(0)

    max_mb = config.MAX_VIDEO_SIZE_MB if media_type == "video" else config.MAX_AUDIO_SIZE_MB
    if size_bytes > max_mb * 1024 * 1024:
        return False, "", (
            f"File too large. Maximum {max_mb} MB for {media_type} files."
        )
    if size_bytes < 1024:
        return False, "", "File is too small or empty."

    return True, media_type, ""


def save_upload(file: FileStorage, media_type: str) -> Path:
    """Save the uploaded file under uploads/ with a unique name. Returns the Path."""
    ext = get_extension(file.filename)
    unique = f"{uuid.uuid4().hex}.{ext}"
    safe_dir = config.UPLOAD_DIR / media_type
    safe_dir.mkdir(parents=True, exist_ok=True)
    out_path = safe_dir / secure_filename(unique)
    file.save(out_path)
    return out_path


def cleanup(path: Path) -> None:
    """Best-effort delete of a file."""
    try:
        if path and Path(path).exists():
            Path(path).unlink()
    except Exception:  # noqa: BLE001
        pass


def guess_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "application/octet-stream"
