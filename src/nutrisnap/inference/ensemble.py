"""Weighted model ensemble for NutriSnap inference.

Combines predictions from multiple models (e.g., EfficientNet, ResNet)
using error-weighted averaging.
"""
from typing import Dict, List

import numpy as np
import torch


class NutritionEnsemble:
    """Ensemble of nutrition regressors.

    Implements P3.2: Weighted Ensemble Inference.
    Weights are proportional to 1/MAE computed on validation sets.

    Args:
        models: List of loaded NutritionRegressor models.
        weights: List of weights (e.g. 1/MAE). If None, uniform weights used.
        device: Device to run inference on.
    """

    def __init__(
        self,
        models: List[torch.nn.Module],
        weights: List[float] | None = None,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        self.models = models
        self.device = torch.device(device)

        if weights is None:
            self.weights = torch.ones(len(models), device=self.device) / len(models)
        else:
            w_tensor = torch.tensor(weights, device=self.device, dtype=torch.float32)
            self.weights = w_tensor / w_tensor.sum()

        for m in self.models:
            m.to(self.device)
            m.eval()

    @torch.no_grad()
    def predict(
        self,
        rgb: torch.Tensor,
        depth: torch.Tensor,
        scalars: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:
            rgb: (B, 3, 224, 224)
            depth: (B, 1, 224, 224)
            scalars: (B, 3)
        Returns:
            (B, 4) weighted ensemble prediction.
        """
        rgb = rgb.to(self.device)
        depth = depth.to(self.device)
        scalars = scalars.to(self.device)

        weighted_preds = torch.zeros((rgb.shape[0], 4), device=self.device)

        for model, weight in zip(self.models, self.weights):
            preds = model(rgb, depth, scalars)
            weighted_preds += preds * weight

        # Denormalize from training scale to real units (kcal, grams)
        from nutrisnap.data.dataset import TARGET_SCALES

        weighted_preds = weighted_preds * TARGET_SCALES.to(self.device)

        return weighted_preds
