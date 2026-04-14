"""Tests for NutritionRegressor model architecture."""
import torch
import pytest
from nutrisnap.models.nutrition_regressor import NutritionRegressor, get_model


class TestNutritionRegressor:
    """Verify tensor shapes and flow through the regressor."""

    @pytest.fixture
    def model(self):
        return NutritionRegressor(
            backbone_name="resnet18",
            pretrained=False,  # Speed up tests
            scalar_dims=3,
            output_dims=4
        )

    def test_forward_shape(self, model):
        """Model accepts (B, 4, 224, 224) and (B, 3) and returns (B, 4)."""
        batch_size = 2
        rgbd = torch.randn(batch_size, 4, 224, 224)
        scalars = torch.randn(batch_size, 3)
        
        output = model(rgbd, scalars)
        
        assert output.shape == (batch_size, 4)
        assert not torch.isnan(output).any()

    def test_parameter_count(self, model):
        """ResNet18 backbone should keep parameters around 11M."""
        total_params = sum(p.numel() for p in model.parameters())
        # ResNet18 is ~11.7M
        assert total_params > 10_000_000
        assert total_params < 15_000_000

    def test_get_model_from_config(self):
        """Helper function correctly initializes from dict."""
        config = {
            "model": {
                "backbone": "resnet18",
                "pretrained": False,
                "scalar_dims": 3,
                "output_dims": 4,
                "hidden_dims": [64]
            }
        }
        model = get_model(config)
        assert isinstance(model, NutritionRegressor)
        assert model.head[0].out_features == 64
