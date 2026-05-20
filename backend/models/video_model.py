"""
Lightweight CNN for face-level deepfake detection.

Architecture: MobileNetV3-Small backbone + 2-class head.
Used as an architectural fallback if the HuggingFace pretrained detector
cannot be loaded (e.g. offline demo). Matches the project's FYP claim of
a "lightweight CNN for CPU deployment".
"""

from __future__ import annotations

import torch
import torch.nn as nn
from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights


class LightweightDeepfakeCNN(nn.Module):
    """MobileNetV3-Small with a 2-way classifier head (real=0, fake=1)."""

    def __init__(self, pretrained_backbone: bool = True, num_classes: int = 2):
        super().__init__()
        weights = (
            MobileNet_V3_Small_Weights.DEFAULT if pretrained_backbone else None
        )
        backbone = mobilenet_v3_small(weights=weights)

        # Replace final classifier
        in_features = backbone.classifier[-1].in_features
        backbone.classifier[-1] = nn.Linear(in_features, num_classes)
        self.backbone = backbone

        # ImageNet mean/std for normalisation
        self.register_buffer(
            "mean", torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
        )
        self.register_buffer(
            "std", torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: (B, 3, H, W) with values in [0, 1].
        Returns logits of shape (B, 2).
        """
        x = (x - self.mean) / self.std
        return self.backbone(x)


def load_local_video_model(device: str = "cpu") -> LightweightDeepfakeCNN:
    """Instantiate the fallback model on the given device."""
    model = LightweightDeepfakeCNN(pretrained_backbone=True).to(device).eval()
    return model
