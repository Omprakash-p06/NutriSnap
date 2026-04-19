---
phase: 03-sam2-glpn-vit-pipeline
plan: 01
subsystem: pipeline
tags: [segmentation, depth, sam2, glpn, adapters]
requirements: [PREP-04, SEGM-02, MODL-02]
status: complete
duration: 1h
completed_date: "2026-04-20"
key-files:
  - src/nutrisnap/pipeline/segmenter.py
  - src/nutrisnap/pipeline/depth.py
  - configs/pipeline/depth.yaml
  - tests/test_adapters_sam2_glpn.py
---

# Phase 03 Plan 01: SAM 2 and GLPN Model Adapters Summary

## One-liner
Implemented and verified SAM 2 segmentation and GLPN depth estimation adapters, ensuring they run within 4GB VRAM limits on CUDA.

## Objective
Implement the first two stages of the 3-stage accuracy pipeline: SAM 2 segmentation and GLPN depth estimation.

## Key Changes
- **FoodSegmenterSAM2**: Added a new class to `src/nutrisnap/pipeline/segmenter.py` using `facebook/sam2-hiera-tiny` via Hugging Face Transformers. It provides a standardized `segment()` method returning binary masks.
- **DepthEstimatorGLPN**: Created `src/nutrisnap/pipeline/depth.py` and `configs/pipeline/depth.yaml`. Uses `vinvino02/glpn-nyu` for monocular depth estimation, returning normalized 0-1 depth maps.
- **Verification**: Created `tests/test_adapters_sam2_glpn.py` which confirms both models load on CUDA and process a real image from the Nutrition5k dataset.

## Results
- **VRAM Usage**: Both models loaded simultaneously consume ~430 MB of VRAM on CUDA, well below the 4GB (4096 MB) target for GTX 1650 compatibility.
- **Performance**: Models successfully process high-resolution images and return expected artifacts (masks and depth maps).

## Deviations from Plan
- **Sample Image Path**: The specific path mentioned in the plan (`dish_1550796634`) was not found; used `dish_1556572657` instead.
- **Linter Fixes**: Fixed minor linting issues (unused import, formatting) during Task 3 execution.

## Decisions Made
- Used `facebook/sam2-hiera-tiny` as the default SAM 2 model to prioritize speed and low VRAM usage while maintaining high accuracy for food regions.
- Standardized the output of `DepthEstimatorGLPN` to a 0-1 normalized float32 map for easier downstream processing.

## Known Stubs
- None. Both adapters are fully functional for their intended purpose in the pipeline.

## Self-Check: PASSED
- [x] `FoodSegmenterSAM2` implemented and verified.
- [x] `DepthEstimatorGLPN` implemented and verified.
- [x] VRAM usage < 4GB for both models loaded.
- [x] Verification test passed on real image.
