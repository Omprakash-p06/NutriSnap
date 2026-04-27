# Phase 2 Research: Segmentation & Preprocessing

## Standard Stack

- **Segmentation**: [FoodSAM](https://github.com/jamesjg/FoodSAM) (SAM + Semantic Classifier + Object Detector).
- **Depth Estimation (Single Image Adapter)**: [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2) or MiDaS for generating 16-bit depth from single RGB.
- **Image Processing**: `OpenCV` (cv2) for processing.
  - `cv2.bilateralFilter`: Edge-preserving denoising.
  - `cv2.createCLAHE`: Contrast Limited Adaptive Histogram Equalization.
- **Data Augmentation**: `Albumentations` (ensures identical masks/depth transforms).
- **Format**: `RGBD` (4-channel) saved as `.npy` or `.pt` tensors for Phase 4.

## Architecture Patterns

1. **The Pipeline Flow**:
   - `Input RGB` -> `Denoising (Bilateral)` -> `Contrast Enhancement (CLAHE)`.
   - `Processed RGB` -> `FoodSAM` -> `Food Masks`.
   - `Processed RGB` -> `Monocular Depth Model` -> `Depth Map`.
   - `Combine` -> `RGBD Artifact`.

2. **Adapter Layer**:
   - A thin wrapper `nutrisnap.pipeline.segmenter.FoodSegmenter` to abstract FoodSAM's multi-model complexity.
   - A preprocessing utility `nutrisnap.data.preprocessing` to handle the repeatable CV operations.

## Don't Hand-Roll

- **Segmentation Logic**: Use FoodSAM's internal class-to-mask matching.
- **Depth Estimation**: Do not attempt to calculate volume from 2D geometry alone without a research-backed depth/volume backbone.
- **Image Resizing/Padding**: Use `Albumentations` or `cv2` to ensure aspect-ratio-safe padding (letterboxing) rather than stretching.

## Common Pitfalls

- **16-bit Depth Handling**: Reading raw Nutrition5k depth as 8-bit leads to massive precision loss. Use `cv2.IMREAD_UNCHANGED`.
- **Memory Contention**: FoodSAM + Depth Model together easily exceed 4GB VRAM.
  - *Fix*: Load/Run/Unload strategy or sequential processing with `torch.cuda.empty_cache()` between steps.
- **Alignment Shift**: Preprocessing or augmentations applied to RGB but not Depth/Mask will break downstream regression.

## Code Examples

### Reading 16-bit Depth
```python
import cv2
depth_map = cv2.imread(path, cv2.IMREAD_UNCHANGED) # 16-bit
depth_normalized = depth_map.astype(float) / 10000.0 # Standardize to meters
```

### Preprocessing Block
```python
def preprocess(img):
    img = cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    lab[:,:,0] = clahe.apply(lab[:,:,0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
```

## Confidence Level
- **FoodSAM Integration**: High (well-documented)
- **4GB VRAM Feasibility**: Medium (requires careful cache management)
- **RGBD Single-Image Adaptation**: High (SOTA monocular depth is reliable)
