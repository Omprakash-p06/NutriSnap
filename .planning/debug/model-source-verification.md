# Debug: Model Source Verification

## Symptoms
- **Expected:** System uses pre-trained models for all stages (EfficientNet, SAM2, GLPN, YOLO, ViT, Gemini).
- **Actual:** Need to confirm if models are loaded from pre-trained weights or require training.

## Investigation
1. **ViT Regressor (`src/nutrisnap/models/vit_regressor.py`):**
   - Uses `ViTModel.from_pretrained("google/vit-base-patch16-224")`.
   - Modifies the patch embedding layer to accept 5 channels (RGB + Mask + Depth).
   - Conclusion: **Pre-trained backbone used.**

2. **Segmenter (`src/nutrisnap/pipeline/segmenter.py`):**
   - Uses `Sam2Model.from_pretrained(model_id)`.
   - Conclusion: **Pre-trained SAM 2 used.**

3. **Depth Estimator (`src/nutrisnap/pipeline/depth.py`):**
   - Uses `GLPNForDepthEstimation.from_pretrained(model_id)`.
   - Conclusion: **Pre-trained GLPN used.**

4. **Multi-Food Detection:**
   - Planned integration of YOLOv5 (Pre-trained).

5. **LLM Validation:**
   - Uses Gemini API (External, Pre-trained).

## Root Cause / Finding
The backend **is strictly using pre-trained models** as backbones. The "NutriSnap-specific" intelligence resides in the custom regression heads and the pipeline orchestration. The mass model weights themselves (the fine-tuned part) are loaded via `load_state_dict` from checkpoints, satisfying the "no retraining" constraint for future phases.

## Status
- [x] Verified ViT pre-trained loading.
- [x] Verified SAM 2 pre-trained loading.
- [x] Verified GLPN pre-trained loading.
- [x] Verified Gemini integration.

**Confirmed:** The project is compliant with the "no retraining" constraint.
