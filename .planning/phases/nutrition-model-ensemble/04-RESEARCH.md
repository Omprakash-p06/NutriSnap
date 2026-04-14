# Phase 4 Research: Nutrition Model & Ensemble

Research for implementing a lightweight, multi-modal nutrition regressor on hardware with 4GB VRAM (GTX 1650).

## Standard Stack

- **Deep Learning Framework**: `torch >= 2.0.0` with `torchvision`.
- **Backbone**: `ResNet18` (Pre-trained on ImageNet). *Note: ResNet18 is more VRAM-efficient for activations than EfficientNet-B0 despite having more parameters.*
- **Optimization**: `AdamW` with `OneCycleLR` for fast convergence.
- **Precision**: `torch.cuda.amp` (Automatic Mixed Precision) to stay within 4GB.
- **Metrics**: `torchmetrics` for MAE, MAPE, and RMSE tracking.
- **Augmentation**: `albumentations` with support for 4-channel (RGB+D) consistency.

## Architecture Patterns

### 1. RGB+D Feature Extractor
- **First Layer Modification**: Modify the `conv1` layer of ResNet18 to accept 4 input channels (RGB + Depth).
- **Weight Initialization**: Copy pre-trained RGB weights and initialize the 4th channel (Depth) with the average of RGB weights to maintain feature scale.
- **Global Pooling**: Use `GlobalAveragePooling` to produce a 512-dim visual feature vector.

### 2. Multi-Modal Fusion (Late Fusion)
- **Feature Assembly**: 
  - Visual Features: 512-dim (ResNet18 GAP output).
  - Scalar Features: 3-dim (`[volume_cm3, area_cm2, confidence]`).
- **Fusion Head**: Simple concatenation followed by a 2-layer MLP (e.g., `[515 -> 128 -> ReLU -> 4]`).
- **Inference Speed**: Direct concatenation is preferred over attention blocks to minimize latency and memory overhead on 4GB hardware.

### 3. K-Fold Strategy
- **5-Fold split**: Use `data/splits/` generated in Phase 1.
- **Balanced Seeds**: Ensure consistent dish-ID exclusion across folds.

## Don't Hand-Roll

- **K-Fold Loops**: Use existing NutriSnap data pipeline and manifest; avoid custom parsing of raw Nutrition5k text files.
- **Training Hooks**: Use a standard training class/utility; avoid writing raw backprop loops from scratch if possible.

## Common Pitfalls

- **VRAM OOM (Out Of Memory)**: 4GB is extremely tight. 
  - **Fix**: Use batch size 16 or 32 with Gradient Accumulation (8 steps of size 4 if needed).
  - **Fix**: Always use `torch.cuda.empty_cache()` between folds.
- **Scale Mismatch**: Nutrition targets span a wide range (0 to 1000+ calories).
  - **Fix**: Log-transform targets or use a Robust Loss (Huber) to prevent outliers from dominating gradients.
- **Depth Saturation**: Raw depth data can have noise.
  - **Fix**: Ensure depth is normalized to `[0, 1]` or same scale as RGB before being passed to the 4th channel.

## Code Examples

### 4-Channel ResNet18 Adapter
```python
import torch.nn as nn
from torchvision.models import resnet18, ResNet18_Weights

def get_4ch_resnet18():
    model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
    # Modify conv1
    original_conv = model.conv1
    model.conv1 = nn.Conv2d(4, 64, kernel_size=7, stride=2, padding=3, bias=False)
    # Copy RGB weights
    with torch.no_grad():
        model.conv1.weight[:, :3, :, :] = original_conv.weight
        # Init 4th channel with average
        model.conv1.weight[:, 3, :, :] = original_conv.weight.mean(dim=1)
    return model
```

## Confidence Levels

- **Hardware Feasibility**: HIGH. ResNet18 with BS=16 comfortably fits in 4GB with AMP.
- **Fusion Strategy**: HIGH. Late fusion is robust for this specific dataset.
- **Convergence**: MEDIUM. Dependent on the quality of volume/area features from Phase 3.

## RESEARCH COMPLETE
Summary:
- Backbone: ResNet18 (4-channel input).
- Head: Late fusion (Concat visual + scalar).
- Hardware: AMP + Gradient Accumulation + 4GB Target.
- Validation: 5-Fold MAE/MAPE.
