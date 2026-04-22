"""Balanced Multi-Task NutriSnap Nutrition Regressor (Ensemble Ready).

Supports multiple RGB backbones (EffNet, ResNet), optional Depth branch,
and Attention-based fusion.
"""

import torch
import torch.nn as nn

from nutrisnap.models.backbone import get_backbone
from nutrisnap.models.depth_cnn import DepthCNN
from nutrisnap.models.fusion import ChannelAttentionFusion
from nutrisnap.models.heads import NutritionHeads


class NutritionRegressor(nn.Module):
    """Refined multi-task regressor with flexible backbone and attention fusion.

    Input:
        rgb:     (B, 3, 224, 224)
        depth:   (B, 1, 224, 224)
        scalars: (B, scalar_dims)

    Output:
        (B, 4) -> [calories, fat, carbs, protein]
    """

    def __init__(
        self,
        backbone_name: str = "efficientnet_v2_b0",
        pretrained: bool = True,
        freeze_backbone: bool = True,
        dropout: float = 0.3,
        scalar_dims: int = 3,
        depth_out_dim: int = 64,
        hidden_dims: list[int] | None = None,
        use_attention: bool = True,
    ):
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [512, 256]

        # 1. RGB Backbone
        self.rgb_branch = get_backbone(backbone_name, pretrained, freeze_backbone)

        # 2. Depth Branch
        self.depth_branch = DepthCNN(out_dim=depth_out_dim)

        # 3. Fusion (Phase 2.5: Attention)
        rgb_dim = self.rgb_branch.OUT_DIM
        self.use_attention = use_attention
        if use_attention:
            self.att_fusion = ChannelAttentionFusion(
                rgb_dim, depth_out_dim, scalar_dims
            )

        in_features = rgb_dim + depth_out_dim + scalar_dims

        # 4. Dense Head
        layers: list[nn.Module] = []
        curr = in_features
        for i, h_dim in enumerate(hidden_dims):
            layers.append(nn.Linear(curr, h_dim))
            layers.append(nn.BatchNorm1d(h_dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout > 0 and i < len(hidden_dims) - 1:
                layers.append(nn.Dropout(dropout))
            curr = h_dim
        self.fusion_net = nn.Sequential(*layers)

        # 4 Regression Tasks
        self.heads = NutritionHeads(in_dim=curr)

    def freeze_backbone(self):
        self.rgb_branch.freeze_backbone()

    def unfreeze_last_n_layers(self, n: int = 3):
        self.rgb_branch.unfreeze_last_n_layers(n)

    def unfreeze_all(self):
        self.rgb_branch.unfreeze_all()

    def forward(
        self,
        rgb: torch.Tensor,
        depth: torch.Tensor,
        scalars: torch.Tensor,
    ) -> torch.Tensor:
        rgb_feats = self.rgb_branch(rgb)
        depth_feats = self.depth_branch(depth)

        if self.use_attention:
            fused_vector = self.att_fusion(rgb_feats, depth_feats, scalars)
        else:
            fused_vector = torch.cat([rgb_feats, depth_feats, scalars], dim=1)

        shared = self.fusion_net(fused_vector)
        return self.heads(shared)


def get_model(config: dict) -> NutritionRegressor:
    """Create NutritionRegressor from a loaded YAML config dict."""
    m = config.get("model", {})
    return NutritionRegressor(
        backbone_name=m.get("backbone", "efficientnet_v2_b0"),
        pretrained=m.get("pretrained", True),
        freeze_backbone=m.get("freeze_backbone", True),
        dropout=m.get("dropout", 0.3),
        scalar_dims=m.get("scalar_dims", 3),
        depth_out_dim=m.get("depth_cnn_hidden", 64),
        hidden_dims=m.get("hidden_dims", [512, 256]),
        use_attention=m.get("use_attention", True),
    )
