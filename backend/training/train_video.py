"""
Video deepfake detector training script.

UPDATED for Priority 3-equivalent video retrain:
  - Heavier realism augmentations (JPEG compression, blur, downscale/upscale,
    stronger color jitter) to simulate WhatsApp/phone video conditions.
  - Supports warm-start via --init-from to fine-tune an existing checkpoint.
  - Lower default LR (1e-5) suitable for fine-tuning, not from-scratch.

Expected dataset layout (unchanged):

    dataset/
        train/
            real/*.jpg
            fake/*.jpg
        val/
            real/*.jpg
            fake/*.jpg

Run (warm-start fine-tune):
    python -m training.train_video \\
        --data ./datasets_video \\
        --init-from ./video_finetuned.pt \\
        --epochs 8 --batch 32 --lr 1e-5 \\
        --out ./video_finetuned_v2.pt
"""

from __future__ import annotations

import argparse
import io
import random
import time
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image, ImageFilter
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from models.video_model import LightweightDeepfakeCNN


# --------------------------------------------------------------------------- #
#               Custom realism augmentations (JPEG, blur, downscale)          #
# --------------------------------------------------------------------------- #
class RandomJPEGCompression:
    """
    Re-encode the PIL image as JPEG at a random quality, then decode.
    This injects real JPEG/H.264-like blocking artefacts into training,
    teaching the model that compression is not a deepfake cue.
    """
    def __init__(self, quality_range=(30, 80), p=0.5):
        self.quality_range = quality_range
        self.p = p

    def __call__(self, img: Image.Image) -> Image.Image:
        if random.random() > self.p:
            return img
        q = random.randint(*self.quality_range)
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=q)
        buf.seek(0)
        return Image.open(buf).convert("RGB")


class RandomDownscaleUpscale:
    """
    Downscale to a random small size, then upscale back to the original.
    Simulates low-resolution video being shown at a higher resolution.
    """
    def __init__(self, scale_range=(0.4, 0.8), p=0.4):
        self.scale_range = scale_range
        self.p = p

    def __call__(self, img: Image.Image) -> Image.Image:
        if random.random() > self.p:
            return img
        w, h = img.size
        s = random.uniform(*self.scale_range)
        new_w, new_h = max(64, int(w * s)), max(64, int(h * s))
        small = img.resize((new_w, new_h), Image.BILINEAR)
        return small.resize((w, h), Image.BILINEAR)


class RandomGaussianBlur:
    def __init__(self, radius_range=(0.0, 1.5), p=0.3):
        self.radius_range = radius_range
        self.p = p

    def __call__(self, img: Image.Image) -> Image.Image:
        if random.random() > self.p:
            return img
        r = random.uniform(*self.radius_range)
        if r < 0.05:
            return img
        return img.filter(ImageFilter.GaussianBlur(radius=r))


# --------------------------------------------------------------------------- #
#                              Data loaders                                   #
# --------------------------------------------------------------------------- #
def build_loaders(data_dir: Path, batch: int, workers: int = 2):
    # ---- Training: aggressive realism augmentations ----
    train_tf = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomResizedCrop(224, scale=(0.80, 1.0)),
        transforms.RandomHorizontalFlip(),
        # Realism — compression / blur / downscale / lighting
        RandomJPEGCompression(quality_range=(30, 80), p=0.5),
        RandomDownscaleUpscale(scale_range=(0.4, 0.8), p=0.4),
        RandomGaussianBlur(radius_range=(0.0, 1.5), p=0.3),
        transforms.ColorJitter(brightness=0.25, contrast=0.25,
                               saturation=0.20, hue=0.05),
        transforms.ToTensor(),
    ])

    # ---- Validation: no augmentation ----
    val_tf = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
    ])

    train_ds = datasets.ImageFolder(str(data_dir / "train"), transform=train_tf)
    val_ds = datasets.ImageFolder(str(data_dir / "val"), transform=val_tf)

    # Remap so fake=1, real=0 regardless of alphabetical order
    fake_idx = train_ds.class_to_idx["fake"]

    def _remap(ds):
        ds.samples = [(p, 1 if y == fake_idx else 0) for (p, y) in ds.samples]
        ds.targets = [y for _, y in ds.samples]
        return ds

    train_ds = _remap(train_ds)
    val_ds = _remap(val_ds)

    train_loader = DataLoader(train_ds, batch_size=batch, shuffle=True,
                              num_workers=workers, pin_memory=False)
    val_loader = DataLoader(val_ds, batch_size=batch, shuffle=False,
                            num_workers=workers, pin_memory=False)

    n_real = sum(1 for _, y in train_ds.samples if y == 0)
    n_fake = sum(1 for _, y in train_ds.samples if y == 1)
    print(f"[loader] train: real={n_real}  fake={n_fake}")

    return train_loader, val_loader


# --------------------------------------------------------------------------- #
#                                 Train                                       #
# --------------------------------------------------------------------------- #
def train(args):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Training on: {device}")

    model = LightweightDeepfakeCNN(pretrained_backbone=True).to(device)

    if args.init_from:
        init_path = Path(args.init_from)
        if not init_path.is_file():
            raise FileNotFoundError(f"--init-from not found: {init_path}")
        state = torch.load(str(init_path), map_location=device)
        try:
            model.load_state_dict(state)
            print(f"[warm-start] Loaded weights from {init_path}")
        except Exception as exc:
            raise RuntimeError(
                f"Checkpoint at {init_path} does not match current "
                f"LightweightDeepfakeCNN architecture: {exc}"
            )
    else:
        print("[cold-start] Training from ImageNet-pretrained backbone only")

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)
    criterion = nn.CrossEntropyLoss()

    train_loader, val_loader = build_loaders(Path(args.data), args.batch, args.workers)

    best_acc = 0.0
    best_epoch = 0
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

        train_loss = running / max(1, total)
        train_acc = correct / max(1, total)

        # ---- Validation ----
        model.eval()
        v_correct, v_total = 0, 0
        # Per-class accuracy to detect bias
        v_real_correct, v_real_total = 0, 0
        v_fake_correct, v_fake_total = 0, 0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                preds = model(x).argmax(1)
                v_correct += (preds == y).sum().item()
                v_total += x.size(0)
                v_real_correct += ((preds == y) & (y == 0)).sum().item()
                v_real_total   += (y == 0).sum().item()
                v_fake_correct += ((preds == y) & (y == 1)).sum().item()
                v_fake_total   += (y == 1).sum().item()

        val_acc = v_correct / max(1, v_total)
        val_real_acc = v_real_correct / max(1, v_real_total)
        val_fake_acc = v_fake_correct / max(1, v_fake_total)

        dt = time.time() - t0
        print(f"epoch {epoch:02d}/{args.epochs}  "
              f"loss={train_loss:.4f}  train_acc={train_acc:.3f}  "
              f"val_acc={val_acc:.3f}  (real={val_real_acc:.3f}  fake={val_fake_acc:.3f})  "
              f"lr={opt.param_groups[0]['lr']:.2e}  ({dt:.1f}s)")

        if val_acc > best_acc:
            best_acc = val_acc
            best_epoch = epoch
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), args.out)
            print(f"  ↳ saved new best: {args.out} (val_acc={val_acc:.3f})")

    print(f"\nDone. Best val_acc = {best_acc:.3f} at epoch {best_epoch}")
    print(f"Final model saved to: {args.out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--init-from", default=None,
                    help="Path to existing .pt to warm-start from")
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--out", default="./storage/video_finetuned.pt")
    args = ap.parse_args()
    train(args)


if __name__ == "__main__":
    main()