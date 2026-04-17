"""Multi-task regression heads for NutriSnap nutrition prediction."""
import torch
import torch.nn as nn
import torch.nn.functional as F


class NutritionHeads(nn.Module):
    """Four independent regression heads sharing an input feature dimension.

    Each head is a single Linear(in_dim, 1) layer with a Leaky ReLU clamp
    (nutrition values are always non-negative).

    Args:
        in_dim: Input feature dimension from the fusion layer (default 256).
    """

    TASK_NAMES = ["calories", "fat", "carbs", "protein"]

    def __init__(self, in_dim: int = 256):
        super().__init__()
        self.calorie_head = nn.Linear(in_dim, 1)
        self.fat_head = nn.Linear(in_dim, 1)
        self.carb_head = nn.Linear(in_dim, 1)
        self.protein_head = nn.Linear(in_dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, in_dim) fused feature tensor.
        Returns:
            (B, 4) predictions: [calories, fat, carbs, protein].
        """
        cal = F.leaky_relu(self.calorie_head(x), negative_slope=0.01)
        fat = F.leaky_relu(self.fat_head(x), negative_slope=0.01)
        carb = F.leaky_relu(self.carb_head(x), negative_slope=0.01)
        prot = F.leaky_relu(self.protein_head(x), negative_slope=0.01)
        return torch.cat([cal, fat, carb, prot], dim=1)
