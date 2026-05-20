"""
Temperature scaling — a standard post-hoc calibration method.

Learn a single scalar T such that softmax(logits / T) has well-calibrated
probabilities. Applied AFTER training, BEFORE deployment. Does not change
classification decisions but produces probabilities that actually mean what
they claim: 0.8 really corresponds to ~80% empirical accuracy.

Reference: Guo et al., "On Calibration of Modern Neural Networks", ICML 2017.
"""

from __future__ import annotations
import argparse
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from models.video_model import LightweightDeepfakeCNN


def learn_temperature(logits: torch.Tensor, labels: torch.Tensor) -> float:
    """Optimize a single T to minimize NLL on val set."""
    T = nn.Parameter(torch.ones(1) * 1.5)
    optimizer = torch.optim.LBFGS([T], lr=0.1, max_iter=100)

    def closure():
        optimizer.zero_grad()
        loss = F.cross_entropy(logits / T, labels)
        loss.backward()
        return loss

    optimizer.step(closure)
    return float(T.detach().item())


def calibrate_video(ckpt_path: Path, val_dir: Path) -> float:
    tf = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
    ])
    ds = datasets.ImageFolder(str(val_dir), transform=tf)
    fake_idx = ds.class_to_idx["fake"]
    ds.samples = [(p, 1 if y == fake_idx else 0) for p, y in ds.samples]
    loader = DataLoader(ds, batch_size=32, shuffle=False, num_workers=2)

    model = LightweightDeepfakeCNN(pretrained_backbone=False)
    model.load_state_dict(torch.load(str(ckpt_path), map_location="cpu"))
    model.eval()

    all_logits, all_labels = [], []
    with torch.no_grad():
        for xb, yb in loader:
            all_logits.append(model(xb))
            all_labels.append(yb)
    logits = torch.cat(all_logits)
    labels = torch.cat(all_labels)

    T = learn_temperature(logits, labels)
    print(f"Video temperature: T = {T:.3f}")
    return T


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video-ckpt", default="./storage/video_finetuned.pt")
    ap.add_argument("--video-val",  default="../datasets/video/val")
    args = ap.parse_args()

    T_v = calibrate_video(Path(args.video_ckpt), Path(args.video_val))
    # Save to a tiny file the loader can read
    with open("./storage/video_temperature.txt", "w") as fh:
        fh.write(f"{T_v:.6f}\n")
    print(f"Saved video T to ./storage/video_temperature.txt")