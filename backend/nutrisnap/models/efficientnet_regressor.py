import timm
import torch
import torch.nn as nn


class EfficientNetRegressor(nn.Module):
    """EfficientNetV2-B0 based mass regressor for 5-channel composite images.

    Backbone: tf_efficientnetv2_b0
    Inputs: (B, 5, 224, 224) - RGB (3) + Mask (1) + Depth (1)
    Output: (B, 1) - predicted mass in grams
    """

    def __init__(self, num_channels=5, volume_dim=128):
        super().__init__()

        # Learnable projection from 5 -> 3 channels to use pre-trained 3-channel weights
        self.channel_proj = nn.Conv2d(num_channels, 3, kernel_size=1)

        # Load pre-trained EfficientNetV2-B0 (without classifier)
        self.backbone = timm.create_model(
            "tf_efficientnetv2_b0", pretrained=True, num_classes=0
        )

        # Get the number of features from the backbone (1280 for B0)
        self.num_features = self.backbone.num_features

        # Volume projection: scalar -> Linear(1, 128) -> BatchNorm -> LeakyReLU
        self.volume_proj = nn.Sequential(
            nn.Linear(1, volume_dim),
            nn.BatchNorm1d(volume_dim),
            nn.LeakyReLU(0.1),
            nn.Dropout(0.1),
        )

        # Fusion head: backbone features + volume features -> predict log1p(mass)
        self.fusion = nn.Sequential(
            nn.Linear(self.num_features + volume_dim, 512),
            nn.BatchNorm1d(512),
            nn.LeakyReLU(0.1),
            nn.Dropout(0.2),
            nn.Linear(512, 1),
        )

    def forward(self, pixel_values, volume=None):
        """
        Args:
            pixel_values (torch.Tensor): (B, 5, 224, 224) composite tensor.
            volume (torch.Tensor): (B, 1) scalar volume feature.
        Returns:
            torch.Tensor: (B, 1) predicted log(mass).
        """
        # 1. Project 5 channels to 3
        x = self.channel_proj(pixel_values)

        # 2. Extract backbone features (B, 1280)
        features = self.backbone(x)

        # 3. Process volume feature (B, 128)
        if volume is not None:
            # Use log1p to compress the large volume range
            norm_volume = torch.log1p(volume)
            v_feat = self.volume_proj(norm_volume)
        else:
            # Fallback
            v_feat = torch.zeros((features.shape[0], 128), device=features.device)

        # 4. Concatenate and regress
        combined = torch.cat((features, v_feat), dim=1)
        return self.fusion(combined)
