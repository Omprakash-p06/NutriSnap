import torch
import torch.nn as nn
from transformers import ViTConfig, ViTModel


class ViTRegressor(nn.Module):
    """ViT-based mass regressor for 5-channel composite images.

    Backbone: ViT (e.g. google/vit-base-patch16-224)
    Inputs: (B, 5, 224, 224) - RGB (3) + Mask (1) + Depth (1)
    Output: (B, 1) - predicted mass in grams
    """

    def __init__(self, model_name="google/vit-base-patch16-224", pretrained=True):
        super().__init__()

        if pretrained:
            self.vit = ViTModel.from_pretrained(model_name)
        else:
            config = ViTConfig.from_pretrained(model_name)
            self.vit = ViTModel(config)

        # 1. Update config to 5 channels
        self.vit.config.num_channels = 5

        # 2. Modify the first layer (patch embedding) to accept 5 channels
        # The original patch_embeddings.projection is a Conv2d(3, hidden_size, kernel_size=16, stride=16)
        old_proj = self.vit.embeddings.patch_embeddings.projection

        # In some versions of transformers, after from_pretrained, the config
        # might already have been used to set internal attributes.
        # But we must ensure the projection layer matches our 5-channel input.

        new_proj = nn.Conv2d(
            in_channels=5,
            out_channels=old_proj.out_channels,
            kernel_size=old_proj.kernel_size,
            stride=old_proj.stride,
            padding=old_proj.padding,
        )

        # Initialize new weights: first 3 channels from old, next 2 zero-initialized or small random
        with torch.no_grad():
            # Ensure we only copy if the source has at least 3 channels
            n_src = old_proj.weight.shape[1]
            n_copy = min(n_src, 3)
            new_proj.weight[:, :n_copy, :, :] = old_proj.weight[:, :n_copy, :, :]
            # Remaining channels (Mask and Depth) - initialized with small values
            if new_proj.weight.shape[1] > n_copy:
                new_proj.weight[:, n_copy:, :, :] = (
                    torch.randn_like(new_proj.weight[:, n_copy:, :, :]) * 0.01
                )
            new_proj.bias = old_proj.bias

        self.vit.embeddings.patch_embeddings.projection = new_proj
        # In some versions of transformers, num_channels is cached in the embeddings object
        if hasattr(self.vit.embeddings.patch_embeddings, "num_channels"):
            self.vit.embeddings.patch_embeddings.num_channels = 5

        # Regression head with Fusion
        # volume: scalar -> Linear(1, 128) -> BatchNorm -> LeakyReLU
        self.volume_proj = nn.Sequential(
            nn.Linear(1, 128), nn.BatchNorm1d(128), nn.LeakyReLU(0.1), nn.Dropout(0.1)
        )

        self.fusion_layer = nn.Linear(self.vit.config.hidden_size + 128, 256)
        self.head = nn.Sequential(
            nn.BatchNorm1d(256),
            nn.LeakyReLU(0.1),
            nn.Dropout(0.2),
            nn.Linear(256, 1),
        )

    def forward(self, pixel_values, volume=None):
        """
        Args:
            pixel_values (torch.Tensor): (B, 5, 224, 224) composite tensor.
            volume (torch.Tensor): (B, 1) scalar volume feature.
        Returns:
            torch.Tensor: (B, 1) predicted log(mass).
        """
        if self.vit.config.num_channels != pixel_values.shape[1]:
            self.vit.config.num_channels = pixel_values.shape[1]

        outputs = self.vit(pixel_values=pixel_values)
        cls_token = outputs.last_hidden_state[:, 0, :]

        if volume is not None:
            # Use log1p to compress the large volume range
            norm_volume = torch.log1p(volume)
            v_feat = self.volume_proj(norm_volume)
        else:
            # Fallback
            v_feat = torch.zeros((cls_token.shape[0], 128), device=cls_token.device)

        combined = torch.cat((cls_token, v_feat), dim=1)
        fused = self.fusion_layer(combined)
        return self.head(fused)
