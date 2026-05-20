"""
Deeptection backend configuration.
Centralised settings for paths, limits, model identifiers and runtime flags.
"""

import os
from pathlib import Path


# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
HISTORY_DIR = BASE_DIR / "history"
STORAGE_DIR = BASE_DIR / "storage"        # cached model weights live here
LOG_FILE = HISTORY_DIR / "history.json"

for d in (UPLOAD_DIR, HISTORY_DIR, STORAGE_DIR):
    d.mkdir(parents=True, exist_ok=True)


# ---------- File constraints ----------
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}
ALLOWED_AUDIO_EXTENSIONS = {"wav", "mp3", "m4a", "flac", "ogg"}

MAX_VIDEO_SIZE_MB = 50
MAX_AUDIO_SIZE_MB = 20
MAX_VIDEO_DURATION_SEC = 180  # 3 minutes


# ---------- Video preprocessing ----------
VIDEO_FRAME_SAMPLE_COUNT = 16          # frames sampled per video for inference
VIDEO_FACE_CROP_SIZE = 224             # model input size
VIDEO_MIN_FACE_CONFIDENCE = 0.5
VIDEO_BLUR_THRESHOLD = 80.0            # Laplacian variance threshold


# ---------- Audio preprocessing ----------
AUDIO_TARGET_SR = 16000
AUDIO_CLIP_SECONDS = 6.0               # pad/trim target
AUDIO_N_MFCC = 40
AUDIO_N_MELS = 128
AUDIO_N_FFT = 1024
AUDIO_HOP_LENGTH = 256
AUDIO_MIN_RMS = 0.0015                 # gate for "silent" input

# ---------- Model source policy ----------
# "auto"  (default) — prefer local trained checkpoints; fall back to HF, then untrained.
# "local"           — use only local checkpoints. Error if missing.
# "hf"              — use only HuggingFace models. Error if offline.
#
# Override at runtime with DEEPTECTION_MODEL_SOURCE={auto|local|hf}.
MODEL_SOURCE = os.getenv("DEEPTECTION_MODEL_SOURCE", "auto").strip().lower()
if MODEL_SOURCE not in ("auto", "local", "hf"):
    MODEL_SOURCE = "auto"

# Legacy compatibility — DEEPTECTION_USE_LOCAL=1 still forces local mode.
if os.getenv("DEEPTECTION_USE_LOCAL", "0") == "1":
    MODEL_SOURCE = "local"

# Paths to fine-tuned checkpoints produced by training/train_video.py
# and training/train_audio.py. If these exist, "auto" mode uses them.
VIDEO_CHECKPOINT_PATH = STORAGE_DIR / "video_finetuned.pt"
AUDIO_CHECKPOINT_PATH = STORAGE_DIR / "audio_finetuned.pt"

# ---------- Model identifiers (HuggingFace) ----------
# These are public, CPU-friendly pretrained deepfake detectors.
# If download fails at runtime, the loader falls back to a locally-initialised
# lightweight architecture so the demo never breaks.
VIDEO_MODEL_HF = os.getenv(
    "DEEPTECTION_VIDEO_MODEL",
    "prithivMLmods/Deep-Fake-Detector-Model",
)
AUDIO_MODEL_HF = os.getenv(
    "DEEPTECTION_AUDIO_MODEL",
    "MelodyMachine/Deepfake-audio-detection-V2",
)


# ---------- Decision engine thresholds ----------
# Final fused score is in [0, 1] where 1 = fake.
DECISION_FAKE_THRESHOLD = 0.62
DECISION_REAL_THRESHOLD = 0.42
DECISION_CONFIDENCE_MIN = 0.50
DECISION_MODALITY_CONFLICT = 0.40
FUSION_VIDEO_WEIGHT = 0.5
FUSION_AUDIO_WEIGHT = 0.5

# ---------- Confidence-aware fusion (new) ----------
STRONG_FAKE_THRESHOLD = 0.80      # above this, a modality can "override" fusion
STRONG_RELIABLE_MIN   = 0.40      # …but only if its reliability is at least this high

# ---------- Per-modality calibration (revised) ----------
CALIBRATION_ENABLED = os.getenv("DEEPTECTION_CALIBRATE", "1") == "1"

# Previously 0.05 / 0.15. New values:
#   Video: no offset — test AUC 0.939 is genuine; calibration was over-correcting
#          on out-of-domain real footage and causing false negatives on real deepfakes.
#   Audio: 0.20 — the audio model is severely out-of-distribution on music and
#          non-ASVspoof speech. We still subtract, but do not let the subtracted
#          score trigger a real-override on its own (see STRONG_REAL_* below).
VIDEO_SCORE_OFFSET = 0.00
AUDIO_SCORE_OFFSET = 0.00

# ---------- Override thresholds (revised) ----------
# Fake override: easier to trigger on video (the trustworthier modality),
#                harder to trigger on audio (the noisier one).
STRONG_FAKE_VIDEO = 0.85
STRONG_FAKE_AUDIO = 0.90

# Real override: ONLY triggers when BOTH modalities clearly agree it's real.
# The previous design let a single strong-real modality flip the verdict;
# that caused false negatives on single-modality attacks (your cases 1, 2, 4).
STRONG_REAL_VIDEO = 0.20
STRONG_REAL_AUDIO = 0.15


# ---------- Video ensemble (asymmetric two-model pipeline) ----------
# When enabled, video inference runs BOTH the local fine-tuned model and
# the HuggingFace baseline, then combines them via the rule set in
# inference/video_inference.py to reduce false positives on real video.
VIDEO_ENSEMBLE = os.getenv("DEEPTECTION_VIDEO_ENSEMBLE", "1") == "1"

# Thresholds for the combination rules.
ENSEMBLE_REAL_THRESHOLD = 0.30   # below this, model is "saying real"
ENSEMBLE_FAKE_THRESHOLD = 0.70   # above this, model is "saying fake"

# ---------- Analysis modes (user-facing scenarios) ----------
# Each mode maps to internal source choices for video and audio.
# Video is always the ensemble — only audio source switches by mode.
ANALYSIS_MODES = {
    "daily": {
        "label":        "Daily Message",
        "video_source": None,          # None = ensemble (auto)
        "audio_source": "local",       # our trained model — robust to phone audio
    },
    "clear_media": {
        "label":        "Clear Media",
        "video_source": None,          # None = ensemble (auto)
        "audio_source": "hf",          # HF baseline — better on studio-clean speech
    },
}
DEFAULT_ANALYSIS_MODE = "daily"


# ---------- Flask ----------
SECRET_KEY = os.getenv("DEEPTECTION_SECRET", "deeptection-dev-secret")
# Max HTTP body size (bit higher than max video to allow headers)
MAX_CONTENT_LENGTH = (MAX_VIDEO_SIZE_MB + 4) * 1024 * 1024
CORS_ORIGINS = os.getenv(
    "DEEPTECTION_CORS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
).split(",")


# ---------- Runtime ----------
DEVICE = "cpu"                          # CPU-only per project constraint
HISTORY_MAX_ENTRIES = 200

