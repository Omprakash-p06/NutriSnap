"""Multi-task regression heads for NutriSnap nutrition prediction."""
import torch
import torch.nn as nn


class NutritionHeads(nn.Module):
    """Four independent regression heads sharing an input feature dimension.

    Each head is a single Linear(in_dim, 1) layer with a ReLU clamp
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
        cal = torch.relu(self.calorie_head(x))
        fat = torch.relu(self.fat_head(x))
        carb = torch.relu(self.carb_head(x))
        prot = torch.relu(self.protein_head(x))
        return torch.cat([cal, fat, carb, prot], dim=1)
