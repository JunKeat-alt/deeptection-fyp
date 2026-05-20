"""
Audio preprocessing pipeline.

Produces:
  * waveform at 16 kHz mono (for wav2vec2-style models)
  * log-mel spectrogram (for CNN models)
  * MFCC features (for MFCC-CNN fallback)
  * a quality dict indicating silence / shortness / noise
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

import librosa
import numpy as np
import torch

import config

log = logging.getLogger("deeptection.preproc.audio")

def _is_speech(y: np.ndarray, sr: int) -> tuple[bool, str]:
    """
    Lightweight speech-presence heuristic. Returns (is_speech, reason).

    Goal: reject music, silence, and pure noise BEFORE the deepfake model
    sees them, because the model was trained on speech only and gives
    misleading high P(fake) on non-speech inputs.
    """
    if y.size < sr * 0.5:
        return False, "too_short_for_speech_check"

    # 1. Zero-crossing rate — speech ~0.05-0.15; music typically lower, noise higher
    zcr = librosa.feature.zero_crossing_rate(y, frame_length=1024, hop_length=256).mean()

    # 2. Spectral flatness — speech is harmonic (low flatness ~0.01-0.15);
    #    music varies; white noise ~1.0
    flat = librosa.feature.spectral_flatness(y=y, n_fft=1024, hop_length=256).mean()

    # 3. Harmonic energy ratio — speech has strong harmonic component
    y_harm, y_perc = librosa.effects.hpss(y, margin=2.0)
    harm_energy = float(np.mean(y_harm ** 2))
    total_energy = float(np.mean(y ** 2)) + 1e-9
    harmonic_ratio = harm_energy / total_energy

    # Music is often overwhelmingly harmonic but with different ZCR/flatness
    # signature than speech. Thresholds below are conservative.
    if flat > 0.35:
        return False, "mostly_noise"
    if harmonic_ratio < 0.25:
        return False, "non_harmonic"     # likely percussion or noise
    if zcr < 0.02:
        return False, "possible_music"   # very low ZCR + high harmonics = music
    if zcr > 0.25:
        return False, "possible_noise"

    return True, "ok"


def _compute_rms(y: np.ndarray) -> float:
    if y.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(y.astype(np.float64) ** 2)))


def _pad_or_trim(y: np.ndarray, target_len: int) -> np.ndarray:
    if y.size >= target_len:
        # Take the centre window — often most informative
        start = (y.size - target_len) // 2
        return y[start:start + target_len]
    out = np.zeros(target_len, dtype=np.float32)
    out[: y.size] = y
    return out


def preprocess_audio(path: Path,
                     target_sr: int = config.AUDIO_TARGET_SR,
                     clip_seconds: float = config.AUDIO_CLIP_SECONDS,
                     ) -> Dict:
    """
    Returns:
      {
        "ok": bool,
        "waveform": np.ndarray (float32, 1-D, length = target_sr*clip_seconds),
        "logmel": np.ndarray (n_mels, T),
        "mfcc": np.ndarray (n_mfcc, T),
        "duration_sec": float,
        "quality": {too_quiet, too_short, noisy},
        "error": str | None,
      }
    """
    quality = {"too_quiet": False, "too_short": False, "noisy": False}
    result = {
        "ok": False, "waveform": None, "logmel": None, "mfcc": None,
        "duration_sec": 0.0, "quality": quality, "error": None,
    }

    try:
        y, sr = librosa.load(str(path), sr=target_sr, mono=True)
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"Could not read audio: {exc}"
        return result

    if y is None or y.size == 0:
        result["error"] = "Audio is empty."
        return result

    duration = y.size / float(sr)
    result["duration_sec"] = round(duration, 2)

    # ---- Quality checks ----
    rms = _compute_rms(y)
    if rms < config.AUDIO_MIN_RMS:
        quality["too_quiet"] = True


    if duration < 1.0:
        quality["too_short"] = True
        result["error"] = "Audio is too short (minimum 1 second)."
        return result
    
    # after the RMS / duration checks
    is_speech, speech_reason = _is_speech(y, sr)
    # Relaxed speech filter (Priority 3 fix)
    if not is_speech:
        # Only reject if VERY clearly not usable
        if speech_reason in [ "too_short_for_speech_check"]:
            quality["non_speech"] = True
            quality["non_speech_reason"] = speech_reason

    # crude noise heuristic: high-band spectral flatness
    try:
        flat = float(np.mean(librosa.feature.spectral_flatness(y=y)))
        if flat > 0.55:    # very flat → noise-like
            quality["noisy"] = True
    except Exception:      # noqa: BLE001
        pass

    # ---- Fixed-length waveform ----
    target_len = int(target_sr * clip_seconds)
    wav_fixed = _pad_or_trim(y.astype(np.float32), target_len)

    # ---- Features ----
    mel = librosa.feature.melspectrogram(
        y=wav_fixed, sr=target_sr,
        n_fft=config.AUDIO_N_FFT, hop_length=config.AUDIO_HOP_LENGTH,
        n_mels=config.AUDIO_N_MELS, fmax=target_sr // 2,
    )
    logmel = librosa.power_to_db(mel + 1e-9, ref=np.max)

    mfcc = librosa.feature.mfcc(
        y=wav_fixed, sr=target_sr,
        n_mfcc=config.AUDIO_N_MFCC,
        n_fft=config.AUDIO_N_FFT, hop_length=config.AUDIO_HOP_LENGTH,
    )

    result["ok"] = True
    result["waveform"] = wav_fixed
    result["logmel"] = logmel.astype(np.float32)
    result["mfcc"] = mfcc.astype(np.float32)
    return result


def waveform_to_tensor(waveform: np.ndarray) -> torch.Tensor:
    """Return a (1, T) float32 tensor for HF audio models."""
    return torch.from_numpy(waveform).float().unsqueeze(0)


def logmel_to_tensor(logmel: np.ndarray) -> torch.Tensor:
    """Return a (1, 1, n_mels, T) tensor normalised to roughly zero-mean unit-var."""
    x = logmel.copy()
    x = (x - x.mean()) / (x.std() + 1e-6)
    return torch.from_numpy(x).float().unsqueeze(0).unsqueeze(0)
