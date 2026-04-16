"""RGB backbone wrappers for NutriSnap.

Supports EfficientNetV2-B0 and ResNet-101 via timm.
"""
import torch
import torch.nn as nn

try:
    import timm

    _TIMM_AVAILABLE = True
except ImportError:
    _TIMM_AVAILABLE = False


class BackboneBase(nn.Module):
    """Base class for backbones to ensure common interface."""

    OUT_DIM: int = 0

    def freeze_backbone(self):
        for p in self.parameters():
            p.requires_grad_(False)

    def unfreeze_all(self):
        for p in self.parameters():
            p.requires_grad_(True)

    def unfreeze_last_n_layers(self, n: int = 3):
        raise NotImplementedError


class EfficientNetV2B0Backbone(BackboneBase):
    """EfficientNetV2-B0 feature extractor. Produces 1,280-dim vectors."""

    OUT_DIM = 1280

    def __init__(self, pretrained: bool = True, freeze: bool = False):
        super().__init__()
        if not _TIMM_AVAILABLE:
            raise ImportError("timm is required: pip install timm>=0.9.0")

        self.model = timm.create_model(
            "tf_efficientnetv2_b0",
            pretrained=pretrained,
            num_classes=0,
            global_pool="avg",
        )
        if freeze:
            self.freeze_backbone()

    def unfreeze_last_n_layers(self, n: int = 3):
        blocks = list(self.model.blocks)
        for block in blocks[-n:]:
            for p in block.parameters():
                p.requires_grad_(True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)


class ResNet101Backbone(BackboneBase):
    """ResNet-101 feature extractor. Produces 2,048-dim vectors."""

    OUT_DIM = 2048

    def __init__(self, pretrained: bool = True, freeze: bool = False):
        super().__init__()
        if not _TIMM_AVAILABLE:
            raise ImportError("timm is required")

        self.model = timm.create_model(
            "resnet101",
            pretrained=pretrained,
            num_classes=0,
            global_pool="avg",
        )
        if freeze:
            self.freeze_backbone()

    def unfreeze_last_n_layers(self, n: int = 1):
        # resnet layers: layer1, layer2, layer3, layer4
        layers = [
            self.model.layer4,
            self.model.layer3,
            self.model.layer2,
            self.model.layer1,
        ]
        for layer in layers[:n]:
            for p in layer.parameters():
                p.requires_grad_(True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)


def get_backbone(
    name: str = "efficientnet_v2_b0", pretrained: bool = True, freeze: bool = False
) -> BackboneBase:
    """Factory to create backbones by name."""
    if name == "efficientnet_v2_b0":
        return EfficientNetV2B0Backbone(pretrained=pretrained, freeze=freeze)
    elif name == "resnet101":
        return ResNet101Backbone(pretrained=pretrained, freeze=freeze)
    else:
        raise ValueError(
            f"Unknown backbone: {name}. Options: efficientnet_v2_b0, resnet101"
        )
