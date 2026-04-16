"""Fusion modules for RGB, Depth, and Scalar features."""
import torch
import torch.nn as nn


class ChannelAttentionFusion(nn.Module):
    """Refined Squeeze-and-Excitation style fusion for multiple modalities.

    Learns to weight RGB, Depth, and Scalar features based on their
    global context.
    """

    def __init__(
        self, rgb_dim: int, depth_dim: int, scalar_dim: int, reduction: int = 16
    ):
        super().__init__()
        self.total_dim = rgb_dim + depth_dim + scalar_dim

        self.avg_pool = nn.AdaptiveAvgPool1d(1)
        self.max_pool = nn.AdaptiveMaxPool1d(1)

        self.excitation = nn.Sequential(
            nn.Linear(self.total_dim, self.total_dim // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(self.total_dim // reduction, self.total_dim, bias=False),
            nn.Sigmoid(),
        )

    def forward(
        self, rgb: torch.Tensor, depth: torch.Tensor, scalars: torch.Tensor
    ) -> torch.Tensor:
        """
        Args:
            rgb: (B, rgb_dim)
            depth: (B, depth_dim)
            scalars: (B, scalar_dim)
        Returns:
            (B, total_dim) weighted fused vector.
        """
        combined = torch.cat([rgb, depth, scalars], dim=1)  # (B, total_dim)

        # In 1D vector case, pooling doesn't really apply, but we use the excitation
        # logic to generate per-channel weights.
        weights = self.excitation(combined)
        return combined * weights
