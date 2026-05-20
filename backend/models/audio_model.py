"""
Lightweight CNN for audio deepfake detection.

Matches the project's FYP claim: "CNN on MFCC/spectrogram for audio".
Used as an architectural fallback if the HuggingFace pretrained audio
detector cannot be loaded. Accepts (B, 1, n_mels, T) log-mel spectrograms.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class MelCNN(nn.Module):
    """A compact 4-block CNN operating on log-mel spectrograms."""

    def __init__(self, num_classes: int = 2, in_channels: int = 1):
        super().__init__()

        def block(ci: int, co: int) -> nn.Sequential:
            return nn.Sequential(
                nn.Conv2d(ci, co, kernel_size=3, padding=1, bias=False),
                nn.BatchNorm2d(co),
                nn.ReLU(inplace=True),
                nn.Conv2d(co, co, kernel_size=3, padding=1, bias=False),
                nn.BatchNorm2d(co),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2),
            )

        self.features = nn.Sequential(
            block(in_channels, 32),
            block(32, 64),
            block(64, 128),
            block(128, 128),
        )
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(64, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, 1, n_mels, T) → logits (B, 2)."""
        x = self.features(x)
        x = self.pool(x)
        return self.classifier(x)


def load_local_audio_model(device: str = "cpu") -> MelCNN:
    model = MelCNN().to(device).eval()
    return model
