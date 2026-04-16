# Requirements: NutriSnap

**Defined:** 2026-04-11  
**Updated:** 2026-04-16 — Final architecture locked (3-model ensemble, SAM-LoRA, 3-tier verification)  
**Core Value:** A user can upload a single meal image and receive a realistic, verified nutrition estimate on commodity hardware.

---

## v1 Requirements

### Data Foundation

- [x] **DATA-01**: Developer can ingest and audit Nutrition5k source assets into a reproducible `raw → interim → processed` data flow without silently accepting corrupt or missing files.
- [x] **DATA-02**: Developer can reproduce official train/test split handling without leaking dish instances across dataset boundaries.
- [x] **DATA-03**: Developer can generate a 70/15/15 split (by dish_id) using GroupShuffleSplit from the official test split boundary.
- [x] **DATA-04**: Developer can generate 5-fold stratified cross-validation artifacts (stratified by calorie bins, grouped by dish_id).
- [ ] **DATA-05**: Developer can apply ingredient-mass correction to filter dishes where the sum of component weights deviates more than 5% from the reported total.
- [ ] **DATA-06**: Developer can apply frame filtering from 360° video (1-in-5 frames, quality-ranked) to select best overhead frames per dish.

### Preprocessing

- [x] **PREP-01**: System can preprocess RGB images through the full pipeline: Bilateral Filter → CLAHE (L-channel) → ImageNet normalize → 224×224 tensors saved as `{dish_id}_rgb.pt`.
- [x] **PREP-02**: System can preprocess depth maps: 16-bit → metres → Median filter → TELEA inpainting → Gaussian smooth → min-max normalize → 224×224 tensors saved as `{dish_id}_depth.pt`.
- [x] **PREP-03**: Preprocessing script is resumable — skips dishes that already have both output tensors.
- [ ] **PREP-04**: System applies SAM LoRA fine-tuned segmentation to generate binary food masks; masks are applied to both RGB and depth (background → 0) before tensor save.

### Segmentation

- [x] **SEGM-01**: System can generate food masks for target meal images using the integrated FoodSAM segmenter.
- [ ] **SEGM-02**: SAM is fine-tuned with LoRA adapters on Nutrition5k food masks for food-specific accuracy.

### Model Architecture

- [x] **MODL-01**: Primary model (EfficientNetV2-B0 + DepthCNN dual-branch) can train to predict calories, protein, carbohydrates, and fats from RGB and depth tensors.
- [x] **MODL-02**: Training operates within RTX 3050 / 4GB VRAM using mixed precision (AMP), gradient accumulation (4 steps → effective batch 32), and 3-phase transfer learning.
- [x] **MODL-03**: Uncertainty-weighted multi-task loss (Kendall et al.) automatically balances the four regression tasks via learnable log-variance parameters.
- [ ] **MODL-04**: Secondary model (ResNet101) trained with the same head design for ensemble diversity.
- [ ] **MODL-05**: Tertiary model (Multi-Task CNN + ingredient embedding from component_weights.tsv) implemented and trained.
- [x] **MODL-06**: 3-phase transfer learning schedule: freeze backbone (ep 1–10) → unfreeze last 3 layers (ep 11–20) → full backbone (ep 21+).

### Ensemble

- [ ] **ENS-01**: All three models are trained via 5-fold stratified CV (stratified by calorie bins, grouped by dish_id); best checkpoint saved per fold.
- [ ] **ENS-02**: Weighted ensemble inference aggregates predictions using `weight_i = 1/MAE_i` (normalized) across the 5×3 = 15 model checkpoints.

### Verification

- [x] **VERI-01**: Rule-based validator checks hard bounds (cal 50–1500, prot 1–150, carb 1–250, fat 1–80), calorie-macro consistency (20% tolerance), volume plausibility (50–2000 cm³), and ensemble std dev (> 50 kcal flags high uncertainty).
- [x] **VERI-02**: Gemini 2.0 Flash API fallback is invoked when Tier 1 fails; uses two-step prompt (identify → verify/correct); gracefully no-ops without `GEMINI_API_KEY`.
- [ ] **VERI-03**: Optional USDA FoodData Central cross-reference is triggered after Gemini identifies food items; discrepancy > 20% appends a caution note to the response.

### Evaluation

- [ ] **EVAL-01**: Evaluation reports calorie MAE, MAPE, R², RMSE, Bias, Spearman correlation, and ensemble std dev per model and for the weighted ensemble.
- [ ] **EVAL-02**: Evaluation detects constant-prediction and overfitting failure modes explicitly.
- [ ] **EVAL-03**: Targets: calorie MAE ≤ 40 kcal; MAPE ≤ 12%; R² ≥ 0.85; Spearman ≥ 0.90; ensemble std ≤ 50 kcal.

### API Delivery

- [x] **API-01**: Client submits a meal image to `POST /predict` and receives an accepted `image_id` immediately (non-blocking).
- [x] **API-02**: Client polls `GET /result/{image_id}` until prediction and verification metadata are ready.
- [x] **API-03**: Completed response includes nutrient estimates, confidence level (High/Medium/Low), and a note if Gemini fallback was used. Target inference ≤ 200ms normal; ≤ 3s with Gemini.

### Engineering Quality

- [x] **ENG-01**: Repository uses a config-driven ML project layout with reproducible scripts and documented artifacts.
- [x] **ENG-02**: All preprocessing outputs are tensor files in `data/processed/features/`; splits in `data/splits/`.

---

## v2 Requirements

- **PROD-01**: Support a broader food taxonomy beyond the initial 5–10 dish MVP subset
- **PROD-02**: Polished end-user application layer beyond the backend MVP
- **PROD-03**: Personalized diet planning, recipe recommendation

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | ✅ Completed |
| DATA-02 | Phase 1 | ✅ Completed |
| DATA-03 | Phase 1 | ✅ Completed |
| DATA-04 | Phase 1 | ✅ Completed |
| DATA-05 | Phase 1 | ❌ Pending |
| DATA-06 | Phase 1 | ❌ Pending |
| PREP-01 | Phase 2 | ✅ Completed |
| PREP-02 | Phase 2 | ✅ Completed |
| PREP-03 | Phase 2 | ✅ Completed |
| PREP-04 | Phase 2 | ❌ Pending (SAM-LoRA) |
| SEGM-01 | Phase 2 | ✅ Completed |
| SEGM-02 | Phase 2 | ❌ Pending (SAM-LoRA fine-tune) |
| MODL-01 | Phase 4 | ✅ Completed |
| MODL-02 | Phase 4 | ✅ Completed |
| MODL-03 | Phase 4 | ✅ Completed |
| MODL-04 | Phase 4 | ❌ Pending |
| MODL-05 | Phase 4 | ❌ Pending |
| MODL-06 | Phase 4 | ✅ Completed |
| ENS-01 | Phase 4 | ❌ Pending (needs preprocessing done first) |
| ENS-02 | Phase 4 | ❌ Pending |
| VERI-01 | Phase 5 | ✅ Completed |
| VERI-02 | Phase 5 | ✅ Completed |
| VERI-03 | Phase 5 | ❌ Pending (optional) |
| EVAL-01 | Phase 5 | ❌ Pending |
| EVAL-02 | Phase 5 | ❌ Pending |
| EVAL-03 | Phase 5 | ❌ Pending |
| API-01 | Phase 6 | ✅ Completed |
| API-02 | Phase 6 | ✅ Completed |
| API-03 | Phase 6 | ✅ Completed |
| ENG-01 | All | ✅ Completed |
| ENG-02 | All | ✅ Completed |

---
*Requirements defined: 2026-04-11*  
*Last updated: 2026-04-16 — Final architecture revision (3-model ensemble, SAM-LoRA, 3-tier verification)*
