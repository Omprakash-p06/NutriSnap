"""Tests for NutritionRegressor model architecture."""

import pytest
import torch

from nutrisnap.models.nutrition_regressor import NutritionRegressor, get_model


class TestNutritionRegressor:
    """Verify tensor shapes and flow through the regressor."""

    @pytest.fixture
    def model(self):
        return NutritionRegressor(
            backbone_name="efficientnet_v2_b0",
            pretrained=False,  # Speed up tests
            scalar_dims=3,
        )

    def test_forward_shape(self, model):
        """Model accepts (B, 3, 224, 224), (B, 1, 224, 224), and (B, 3) and returns (B, 4)."""
        batch_size = 2
        rgb = torch.randn(batch_size, 3, 224, 224)
        depth = torch.randn(batch_size, 1, 224, 224)
        scalars = torch.randn(batch_size, 3)

        output = model(rgb, depth, scalars)

        assert output.shape == (batch_size, 4)
        assert not torch.isnan(output).any()

    def test_parameter_count(self, model):
        """EfficientNetV2-B0 backbone should keep parameters around 6-10M."""
        total_params = sum(p.numel() for p in model.parameters())
        # EfficientNetV2-B0 is ~5.9M backbone + heads/fusion
        assert total_params > 5_000_000
        assert total_params < 15_000_000

    def test_get_model_from_config(self):
        """Helper function correctly initializes from dict."""
        config = {
            "model": {
                "backbone": "efficientnet_v2_b0",
                "pretrained": False,
                "scalar_dims": 3,
                "hidden_dims": [64],
            }
        }
        model = get_model(config)
        assert isinstance(model, NutritionRegressor)
        # Check if the last layer of fusion_net has 64 out_features
        # In NutritionRegressor: self.fusion_net = nn.Sequential(*layers)
        # The last layer is curr, which is 64
        # We can check the heads input dim
        assert model.heads.calorie_head.in_features == 64
