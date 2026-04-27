"""Small ConvNet for processing single-channel depth maps.

Produces a 64-dimensional feature vector, lightweight enough to run
alongside the EfficientNetV2-B0 backbone within 4GB VRAM.
"""

import torch
import torch.nn as nn


class DepthCNN(nn.Module):
    """Lightweight depth feature extractor.

    Architecture:
        Conv(1→16) → BN → ReLU → MaxPool
        Conv(16→32) → BN → ReLU → MaxPool
        Conv(32→64) → BN → ReLU → AdaptiveAvgPool(1×1)
        Flatten → Linear → 64-dim output

    Args:
        out_dim: Output feature dimension (default 64).
    """

    OUT_DIM = 64

    def __init__(self, out_dim: int = 64):
        super().__init__()
        self.out_dim = out_dim

        self.features = nn.Sequential(
            # Block 1: 224 → 112
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            # Block 2: 112 → 56
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            # Block 3: 56 → 28
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            # Global average pool
            nn.AdaptiveAvgPool2d((1, 1)),
        )

        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64, out_dim),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, 1, H, W) float32 depth tensor normalized to [0, 1].
        Returns:
            (B, out_dim) feature vector.
        """
        return self.head(self.features(x))
