"""
Video preprocessing pipeline.

Steps:
  1. Open video with OpenCV (also checks duration bound).
  2. Sample N frames uniformly across the video.
  3. Detect face on each frame (MediaPipe preferred, OpenCV Haar fallback).
  4. Crop + resize to `VIDEO_FACE_CROP_SIZE`.
  5. Filter out blurry frames (Laplacian variance).
  6. Return a tensor of shape (N_usable, 3, H, W) plus a quality dict.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import torch

import config

log = logging.getLogger("deeptection.preproc.video")


# ---------------- Face detector abstraction ----------------
class _FaceDetector:
    """Uses MediaPipe if available, otherwise Haar cascade."""

    def __init__(self):
        self._mp = None
        self._haar = None
        try:
            import mediapipe as mp
            self._mp = mp.solutions.face_detection.FaceDetection(
                model_selection=0,    # 0 = close-range (~2m)
                min_detection_confidence=config.VIDEO_MIN_FACE_CONFIDENCE,
            )
            log.info("Using MediaPipe face detector.")
        except Exception as exc:  # noqa: BLE001
            log.info("MediaPipe unavailable (%s); falling back to Haar cascade.", exc)
            haar_path = os.path.join(
                cv2.data.haarcascades, "haarcascade_frontalface_default.xml"
            )
            self._haar = cv2.CascadeClassifier(haar_path)

    def detect(self, frame_bgr: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """Return (x, y, w, h) of the most confident face or None."""
        h, w = frame_bgr.shape[:2]

        if self._mp is not None:
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            res = self._mp.process(rgb)
            if not res.detections:
                return None
            # Pick the detection with the highest score
            det = max(res.detections, key=lambda d: d.score[0] if d.score else 0.0)
            rbb = det.location_data.relative_bounding_box
            x = max(0, int(rbb.xmin * w))
            y = max(0, int(rbb.ymin * h))
            bw = max(1, int(rbb.width * w))
            bh = max(1, int(rbb.height * h))
            return x, y, bw, bh

        # Haar fallback
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = self._haar.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5,
                                            minSize=(60, 60))
        if len(faces) == 0:
            return None
        # Largest face
        return tuple(max(faces, key=lambda f: f[2] * f[3]))


# Singleton (MediaPipe object is heavy to init)
_detector: Optional[_FaceDetector] = None


def _get_detector() -> _FaceDetector:
    global _detector
    if _detector is None:
        _detector = _FaceDetector()
    return _detector


# ---------------- Helpers ----------------
def _variance_of_laplacian(gray: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _expand_box(x: int, y: int, w: int, h: int, W: int, H: int, margin: float = 0.20
                ) -> Tuple[int, int, int, int]:
    mx = int(w * margin)
    my = int(h * margin)
    x1 = max(0, x - mx)
    y1 = max(0, y - my)
    x2 = min(W, x + w + mx)
    y2 = min(H, y + h + my)
    return x1, y1, x2 - x1, y2 - y1


# ---------------- Main entry ----------------
def preprocess_video(path: Path,
                     sample_count: int = config.VIDEO_FRAME_SAMPLE_COUNT,
                     crop_size: int = config.VIDEO_FACE_CROP_SIZE,
                     ) -> Dict:
    """
    Returns a dict:
      {
        "ok": bool,
        "frames": torch.Tensor (N, 3, H, W) float32 in [0,1],  # empty if ok=False
        "num_faces": int,
        "duration_sec": float,
        "quality": {...},
        "error": str | None,
        "has_audio": bool,   # informational; extracted via ffmpeg separately
      }
    """
    quality = {
        "low_face_confidence": False,
        "too_blurry": False,
        "few_frames": False,
    }
    result = {
        "ok": False, "frames": None, "num_faces": 0, "duration_sec": 0.0,
        "quality": quality, "error": None, "has_audio": True,
    }

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        result["error"] = "Could not open video file."
        return result

    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = total / fps if fps > 0 else 0.0
        result["duration_sec"] = round(duration, 2)

        if duration > config.MAX_VIDEO_DURATION_SEC:
            result["error"] = (
                f"Video is too long ({duration:.1f}s). "
                f"Maximum is {config.MAX_VIDEO_DURATION_SEC}s."
            )
            return result
        if total < 2:
            result["error"] = "Video has no readable frames."
            return result

        indices = np.linspace(0, max(0, total - 1), num=sample_count, dtype=int)
        detector = _get_detector()

        crops: List[np.ndarray] = []
        blurry_count = 0
        face_missing = 0

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            H, W = frame.shape[:2]
            box = detector.detect(frame)
            if box is None:
                face_missing += 1
                continue

            x, y, w, h = _expand_box(*box, W=W, H=H, margin=0.22)
            face = frame[y:y + h, x:x + w]
            if face.size == 0:
                face_missing += 1
                continue

            gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
            if _variance_of_laplacian(gray) < config.VIDEO_BLUR_THRESHOLD:
                blurry_count += 1
                # Still include but we'll record quality flag
            face = cv2.resize(face, (crop_size, crop_size), interpolation=cv2.INTER_AREA)
            face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            crops.append(face)

        result["num_faces"] = len(crops)

        if len(crops) == 0:
            result["error"] = "No faces were detected in this video."
            quality["low_face_confidence"] = True
            return result

        if len(crops) < max(4, sample_count // 3):
            quality["few_frames"] = True

        if face_missing >= sample_count // 2:
            quality["low_face_confidence"] = True

        if blurry_count >= len(crops) // 2:
            quality["too_blurry"] = True

        arr = np.stack(crops).astype(np.float32) / 255.0           # (N, H, W, 3)
        tensor = torch.from_numpy(arr).permute(0, 3, 1, 2).contiguous()  # (N, 3, H, W)
        result["ok"] = True
        result["frames"] = tensor
        return result

    finally:
        cap.release()


def extract_audio_from_video(video_path: Path, out_wav: Path,
                             sample_rate: int = config.AUDIO_TARGET_SR) -> bool:
    """
    Extract mono-PCM audio from a video file using ffmpeg (if available on PATH).
    Returns True on success. Falls back silently if ffmpeg is missing.
    """
    import shutil
    import subprocess

    if not shutil.which("ffmpeg"):
        log.info("ffmpeg not found; skipping audio extraction from video.")
        return False

    try:
        cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-vn", "-ac", "1", "-ar", str(sample_rate),
            "-f", "wav", str(out_wav),
        ]
        p = subprocess.run(cmd, capture_output=True, timeout=60)
        return p.returncode == 0 and out_wav.exists() and out_wav.stat().st_size > 1024
    except Exception as exc:  # noqa: BLE001
        log.warning("ffmpeg audio extraction failed: %s", exc)
        return False
