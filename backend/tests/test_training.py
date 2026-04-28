"""Tests for the trainer hardware optimization logic."""

import torch
import torch.nn as nn
from nutrisnap.models.loss import UncertaintyWeightedLoss
from nutrisnap.training.trainer import NutritionTrainer


class SimpleModel(nn.Module):
    def __init__(self):
        super().__init__()
        # Mocking the dual-branch structure
        self.rgb_branch = nn.Sequential(
            nn.Conv2d(3, 8, 3), nn.AdaptiveAvgPool2d(1), nn.Flatten()
        )
        self.rgb_branch.OUT_DIM = 8
        self.depth_branch = nn.Sequential(
            nn.Conv2d(1, 4, 3), nn.AdaptiveAvgPool2d(1), nn.Flatten()
        )
        # 8 (rgb) + 4 (depth) + 3 (scalars) = 15
        self.fc = nn.Linear(15, 4)

    def freeze_backbone(self):
        pass

    def unfreeze_last_n_layers(self, n):
        pass

    def unfreeze_all(self):
        pass

    def forward(self, rgb, depth, scalars):
        r = self.rgb_branch(rgb)
        d = self.depth_branch(depth)
        x = torch.cat([r, d, scalars], dim=1)
        return self.fc(x)


class TestNutritionTrainer:
    """Verify that the trainer correctly handles AMP and Grad Accumulation."""

    def test_train_step_with_amp(self):
        """Forward and backward pass should succeed with AMP enabled."""
        model = SimpleModel()
        criterion = UncertaintyWeightedLoss()
        trainer = NutritionTrainer(
            model=model,
            criterion=criterion,
            device="cpu",  # Use CPU for CI/tests
            use_amp=True,
            grad_accum_steps=2,
        )
        trainer.setup_fold()  # Required to build optimizer

        # Mock batch
        batch = {
            "rgb": torch.randn(2, 3, 32, 32),
            "depth": torch.randn(2, 1, 32, 32),
            "scalar_features": torch.randn(2, 3),
            "targets": torch.randn(2, 4),
        }
        dataloader = [batch, batch, batch, batch]  # 4 steps

        # Run one epoch
        metrics = trainer.train_epoch(dataloader, epoch=1)

        assert "loss" in metrics
        assert metrics["loss"] > 0

    def test_validation_step(self):
        """Validation loop should return MAE and MAPE metrics."""
        model = SimpleModel()
        criterion = UncertaintyWeightedLoss()
        trainer = NutritionTrainer(model=model, criterion=criterion, device="cpu")
        trainer.setup_fold()

        batch = {
            "rgb": torch.randn(2, 3, 32, 32),
            "depth": torch.randn(2, 1, 32, 32),
            "scalar_features": torch.randn(2, 3),
            "targets": torch.randn(2, 4),
            "dish_id": ["dish_1", "dish_2"],
        }
        dataloader = [batch]

        metrics = trainer.validate(dataloader)

        assert "loss" in metrics
        assert "mae" in metrics
        assert "mape" in metrics
        assert len(metrics["mae"]) == 4
        assert len(metrics["mape"]) == 4
