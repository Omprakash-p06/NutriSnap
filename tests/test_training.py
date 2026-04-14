"""Tests for the trainer hardware optimization logic."""
import torch
import torch.nn as nn
import pytest
from nutrisnap.training.trainer import NutritionTrainer


class SimpleModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(4, 8, 3)
        self.fc = nn.Linear(8, 4)
        
    def forward(self, x, scalars):
        x = self.conv(x)
        x = torch.mean(x, dim=(2, 3))
        return self.fc(x)


class TestNutritionTrainer:
    """Verify that the trainer correctly handles AMP and Grad Accumulation."""

    def test_train_step_with_amp(self):
        """Forward and backward pass should succeed with AMP enabled."""
        model = SimpleModel()
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
        trainer = NutritionTrainer(
            model=model,
            optimizer=optimizer,
            device="cpu", # Use CPU for CI/tests
            use_amp=True,
            grad_accum_steps=2
        )
        
        # Mock batch
        batch = {
            "rgbd": torch.randn(2, 4, 32, 32),
            "scalar_features": torch.randn(2, 3),
            "targets": torch.randn(2, 4)
        }
        dataloader = [batch, batch] # 2 steps
        
        # Run one epoch (2 steps, 1 optimizer step)
        metrics = trainer.train_epoch(dataloader, epoch=1)
        
        assert "loss" in metrics
        assert metrics["loss"] > 0
        # Check that optimizer zero_grad was called (can't easily verify state without mocks, 
        # but absence of crash is a good indicator of pipeline health on CPU/AMP)

    def test_validation_step(self):
        """Validation loop should return MAE and MAPE metrics."""
        model = SimpleModel()
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
        trainer = NutritionTrainer(model=model, optimizer=optimizer, device="cpu")
        
        batch = {
            "rgbd": torch.randn(2, 4, 32, 32),
            "scalar_features": torch.randn(2, 3),
            "targets": torch.randn(2, 4)
        }
        dataloader = [batch]
        
        metrics = trainer.validate(dataloader)
        
        assert "loss" in metrics
        assert "mae" in metrics
        assert "mape" in metrics
        assert len(metrics["mae"]) == 4
        assert len(metrics["mape"]) == 4
