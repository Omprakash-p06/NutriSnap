"""Ensemble Inference pipeline for NutriSnap Nutrition Estimation.

Loads 5-fold trained models and provides an aggregated prediction.
"""
from pathlib import Path
from typing import Dict, List, Optional

import torch
import torch.nn as nn
import yaml

from nutrisnap.models.nutrition_regressor import NutritionRegressor
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


class NutritionPredictor:
    """Ensemble predictor that averages results from multiple trained folds."""

    def __init__(
        self,
        checkpoint_dir: str | Path,
        model_config_path: str | Path,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        num_folds: int = 5,
    ):
        self.device = device
        self.checkpoint_dir = Path(checkpoint_dir)

        with open(model_config_path) as f:
            self.model_cfg = yaml.safe_load(f)

        self.models = self._load_ensemble(num_folds)
        logger.info(f"Loaded {len(self.models)} folds for ensembling on {device}")

    def _load_ensemble(self, num_folds: int) -> List[nn.Module]:
        models = []
        for i in range(num_folds):
            ckpt_path = self.checkpoint_dir / f"best_fold_{i}.pth"
            if not ckpt_path.exists():
                logger.warning(
                    f"Fold {i} checkpoint not found at {ckpt_path}. Skipping."
                )
                continue

            model = NutritionRegressor(
                backbone_name=self.model_cfg["model"]["backbone"],
                pretrained=False,
                scalar_dims=self.model_cfg["model"]["scalar_dims"],
                hidden_dims=self.model_cfg["model"]["hidden_dims"],
            )

            state = torch.load(ckpt_path, map_location=self.device)
            model.load_state_dict(state["model_state_dict"])
            model.to(self.device)
            model.eval()
            models.append(model)

        return models

    @torch.no_grad()
    def predict(self, rgbd: torch.Tensor, scalars: torch.Tensor) -> Dict[str, float]:
        """Predict nutrition by averaging all fold results.

        Args:
            rgbd: (1, 4, 224, 224) RGBD tensor.
            scalars: (1, 3) Scalar features tensor.

        Returns:
            Dictionary with averaged nutrition values.
        """
        if not self.models:
            raise RuntimeError("No models loaded in ensemble.")

        rgbd = rgbd.to(self.device)
        scalars = scalars.to(self.device)

        rgb = rgbd[:, :3, :, :]
        depth = rgbd[:, 3:, :, :]

        fold_preds = []
        for model in self.models:
            preds = model(rgb, depth, scalars)
            fold_preds.append(preds)

        # Stack and average: (Folds, 1, 4) -> (1, 4)
        avg_preds = torch.mean(torch.stack(fold_preds), dim=0).squeeze(0)

        # [calories, fat, carbs, protein]
        values = avg_preds.cpu().tolist()

        return {
            "calories": values[0],
            "fat": values[1],
            "carbs": values[2],
            "protein": values[3],
        }
