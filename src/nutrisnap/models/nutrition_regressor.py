"""Nutrition Regressor model for NutriSnap.

Combines a 4-channel ResNet18 backbone with a multi-modal fusion head
to predict calories and macronutrients from RGBD images and scalar features.
"""
import torch
import torch.nn as nn
from torchvision.models import resnet18, ResNet18_Weights


class NutritionRegressor(nn.Module):
    """Multi-modal regressor for calories and macronutrients.

    Input:
        - rgbd: (B, 4, 224, 224) torch.Tensor
        - scalars: (B, 3) torch.Tensor -> [volume, area, confidence]
    Output:
        - predictions: (B, 4) -> [calories, fat, carbs, protein]
    """

    def __init__(
        self,
        backbone_name: str = "resnet18",
        pretrained: bool = True,
        dropout: float = 0.2,
        scalar_dims: int = 3,
        output_dims: int = 4,
        hidden_dims: list[int] = [128, 64],
    ):
        super().__init__()
        
        # 1. Initialize backbone (ResNet18)
        weights = ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
        self.backbone = resnet18(weights=weights)
        
        # 2. Modify first conv layer to accept 4 channels (RGB + Depth)
        original_conv = self.backbone.conv1
        self.backbone.conv1 = nn.Conv2d(
            4, 
            original_conv.out_channels, 
            kernel_size=original_conv.kernel_size, 
            stride=original_conv.stride, 
            padding=original_conv.padding, 
            bias=original_conv.bias is not None
        )
        
        # Transfer weights and initialize 4th channel
        if pretrained:
            with torch.no_grad():
                self.backbone.conv1.weight[:, :3, :, :] = original_conv.weight
                # Initialize 4th channel with the mean of RGB channels
                self.backbone.conv1.weight[:, 3, :, :] = original_conv.weight.mean(dim=1)
        
        # 3. Backbone Feature Extractor (remove fc layer)
        # We use the layers skip the original FC
        self.feature_extractor = nn.Sequential(
            self.backbone.conv1,
            self.backbone.bn1,
            self.backbone.relu,
            self.backbone.maxpool,
            self.backbone.layer1,
            self.backbone.layer2,
            self.backbone.layer3,
            self.backbone.layer4,
            nn.AdaptiveAvgPool2d((1, 1))
        )
        
        # 4. Multi-modal Fusion Head
        # Visual features from ResNet18 are 512-dim
        in_features = 512 + scalar_dims
        
        layers = []
        curr_dims = in_features
        for h_dim in hidden_dims:
            layers.append(nn.Linear(curr_dims, h_dim))
            layers.append(nn.ReLU())
            if dropout > 0:
                layers.append(nn.Dropout(dropout))
            curr_dims = h_dim
            
        layers.append(nn.Linear(curr_dims, output_dims))
        self.head = nn.Sequential(*layers)
        
    def forward(self, rgbd: torch.Tensor, scalars: torch.Tensor) -> torch.Tensor:
        """Forward pass.
        
        Args:
            rgbd: (B, 4, H, W) float32 tensor.
            scalars: (B, scalar_dims) float32 tensor.
        
        Returns:
            (B, 4) predictions.
        """
        # Extract visual features: (B, 512, 1, 1) -> (B, 512)
        vis_feats = self.feature_extractor(rgbd)
        vis_feats = torch.flatten(vis_feats, 1)
        
        # Concatenate with scalar features
        combined = torch.cat([vis_feats, scalars], dim=1)
        
        # Regress
        return self.head(combined)


def get_model(config: dict) -> NutritionRegressor:
    """Helper to create model from config dict."""
    m_cfg = config.get("model", {})
    return NutritionRegressor(
        backbone_name=m_cfg.get("backbone", "resnet18"),
        pretrained=m_cfg.get("pretrained", True),
        dropout=m_cfg.get("dropout", 0.2),
        scalar_dims=m_cfg.get("scalar_dims", 3),
        output_dims=m_cfg.get("output_dims", 4),
        hidden_dims=m_cfg.get("hidden_dims", [128, 64])
    )
