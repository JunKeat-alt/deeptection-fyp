"""
Optional training script — audio deepfake detector (MFCC / log-mel CNN).

Expects a folder layout:

    dataset/
        train/
            real/*.wav (or mp3/flac)
            fake/*.wav
        val/
            real/*.wav
            fake/*.wav

Datasets suitable for this project:
  * Fake-or-Real (FoR)
  * ASVspoof 2019 / 2021
  * WaveFake

Run:
    python -m training.train_audio \\
        --data ./dataset --epochs 15 --batch 32 --out ./storage/audio_finetuned.pt
"""

from __future__ import annotations

import argparse
import random
import time
from pathlib import Path
from typing import List, Tuple

import librosa
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

import config
from models.audio_model import MelCNN


AUDIO_EXTS = (".wav", ".mp3", ".flac", ".ogg", ".m4a")


class AudioFolder(Dataset):
    """Minimal ImageFolder-style dataset for audio."""

    def __init__(self, root: Path, clip_seconds: float = config.AUDIO_CLIP_SECONDS,
                 training: bool = True):
        self.root = Path(root)
        self.training = training
        self.clip_len = int(config.AUDIO_TARGET_SR * clip_seconds)
        self.items: List[Tuple[Path, int]] = []
        for label, cls in enumerate(("real", "fake")):
            d = self.root / cls
            if not d.is_dir():
                continue
            for p in d.rglob("*"):
                if p.suffix.lower() in AUDIO_EXTS:
                    self.items.append((p, label))
        if not self.items:
            raise RuntimeError(f"No audio files under {self.root}")

    def __len__(self):
        return len(self.items)

    def _load_wav(self, path: Path) -> np.ndarray:
        y, _ = librosa.load(str(path), sr=config.AUDIO_TARGET_SR, mono=True)
        if y.size >= self.clip_len:
            if self.training:
                start = random.randint(0, y.size - self.clip_len)
            else:
                start = (y.size - self.clip_len) // 2
            return y[start:start + self.clip_len].astype(np.float32)
        out = np.zeros(self.clip_len, dtype=np.float32)
        out[: y.size] = y
        return out

    def _logmel(self, y: np.ndarray) -> np.ndarray:
        mel = librosa.feature.melspectrogram(
            y=y, sr=config.AUDIO_TARGET_SR,
            n_fft=config.AUDIO_N_FFT, hop_length=config.AUDIO_HOP_LENGTH,
            n_mels=config.AUDIO_N_MELS,
        )
        lm = librosa.power_to_db(mel + 1e-9, ref=np.max).astype(np.float32)
        lm = (lm - lm.mean()) / (lm.std() + 1e-6)
        return lm

    def __getitem__(self, idx):
        path, label = self.items[idx]
        y = self._load_wav(path)
        lm = self._logmel(y)
        x = torch.from_numpy(lm).unsqueeze(0)  # (1, n_mels, T)
        return x, label


def train(args):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Training on: {device}")

    train_ds = AudioFolder(Path(args.data) / "train", training=True)
    val_ds = AudioFolder(Path(args.data) / "val", training=False)
    print(f"train={len(train_ds)}  val={len(val_ds)}")

    train_loader = DataLoader(train_ds, batch_size=args.batch, shuffle=True,
                              num_workers=args.workers)
    val_loader = DataLoader(val_ds, batch_size=args.batch, shuffle=False,
                            num_workers=args.workers)

    model = MelCNN().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)
    criterion = nn.CrossEntropyLoss()

    best = 0.0
    for epoch in range(1, args.epochs + 1):
        model.train()
        t0 = time.time()
        running, correct, total = 0.0, 0, 0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            opt.step()
            running += loss.item() * x.size(0)
            correct += (logits.argmax(1) == y).sum().item()
            total += x.size(0)
        sched.step()

        model.eval()
        v_correct, v_total = 0, 0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                logits = model(x)
                v_correct += (logits.argmax(1) == y).sum().item()
                v_total += x.size(0)
        train_loss = running / max(1, total)
        train_acc = correct / max(1, total)
        val_acc = v_correct / max(1, v_total)
        print(f"epoch {epoch:02d}/{args.epochs}  "
              f"loss={train_loss:.4f}  train_acc={train_acc:.3f}  "
              f"val_acc={val_acc:.3f}  ({time.time() - t0:.1f}s)")

        if val_acc > best:
            best = val_acc
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), args.out)
            print(f"  ↳ saved new best: {args.out} (val_acc={val_acc:.3f})")

    print(f"Done. Best val_acc = {best:.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--out", default="./storage/audio_finetuned.pt")
    args = ap.parse_args()
    train(args)


if __name__ == "__main__":
    main()
