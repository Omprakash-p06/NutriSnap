"""Tests for the ensemble inference logic."""

from unittest.mock import MagicMock, patch

import pytest
import torch
from nutrisnap.pipeline.inference import NutritionPredictor


class TestNutritionPredictor:
    """Verify that the ensemble predictor correctly aggregates results."""

    @pytest.fixture
    def mock_config(self, tmp_path):
        config_path = tmp_path / "model_config.yaml"
        config_path.write_text("""
model:
  backbone: "resnet18"
  scalar_dims: 3
  output_dims: 4
  hidden_dims: [64]
""")
        return config_path

    @patch("nutrisnap.pipeline.inference.torch.load")
    @patch("nutrisnap.pipeline.inference.NutritionRegressor")
    def test_ensemble_averaging(self, mock_regressor, mock_load, mock_config, tmp_path):
        """Verify that predictions from multiple folds are correctly averaged."""
        # Setup: Create dummy checkpoint files
        (tmp_path / "best_fold_0.pth").write_text("dummy")
        (tmp_path / "best_fold_1.pth").write_text("dummy")

        # Mock models
        model1 = MagicMock()
        model1.return_value = torch.tensor([[100.0, 5.0, 10.0, 2.0]])

        model2 = MagicMock()
        model2.return_value = torch.tensor([[200.0, 10.0, 20.0, 4.0]])

        mock_regressor.side_effect = [model1, model2]
        mock_load.return_value = {"model_state_dict": {}}

        # Initialize predictor
        predictor = NutritionPredictor(
            checkpoint_dir=tmp_path,
            model_config_path=mock_config,
            device="cpu",
            num_folds=2,
        )

        # Predict
        rgbd = torch.randn(1, 4, 224, 224)
        scalars = torch.randn(1, 3)
        results = predictor.predict(rgbd, scalars)

        # Assertions
        assert results["calories"] == 150.0
        assert results["fat"] == 7.5
        assert results["carbs"] == 15.0
        assert results["protein"] == 3.0

    def test_empty_ensemble_raises(self, mock_config, tmp_path):
        """Predictor should raise RuntimeError if no folds are loaded."""
        # Use an empty tmp_path (no files exist)

        predictor = NutritionPredictor(
            checkpoint_dir=tmp_path,
            model_config_path=mock_config,
            device="cpu",
            num_folds=2,
        )

        with pytest.raises(RuntimeError, match="No models loaded"):
            predictor.predict(torch.randn(1, 4, 224, 224), torch.randn(1, 3))
