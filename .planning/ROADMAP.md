# Roadmap: NutriSnap

## Overview

NutriSnap v1 builds a multi-layer accuracy pipeline: full RGB+Depth preprocessing, a three-stage pipeline (SAM 2 → GLPN → ViT), and a 3-tier verification layer (rule-based → Gemini API → optional USDA). Target: calorie MAE ≤ 40 kcal on Nutrition5k at ≤ 200ms inference per image on an RTX 3050.

See [`misc/strategy_final_2026-04-16.md`](../misc/strategy_final_2026-04-16.md) for the complete blueprint.

---

## Phase Summary

| Phase | Name | Status |
|-------|------|--------|
| 1 | Foundation & Data Pipeline | ✅ Complete |
| 2 | Foundation Preprocessing | ✅ Complete |
| 3 | SAM 2 -> GLPN -> ViT Pipeline | 🔄 In Progress |
| 4 | Full Dataset Training Run | ❌ Pending |
| 5 | Evaluation & Verification | ❌ Pending |
| 6 | FastAPI Delivery & Quality Hardening | ✅ Complete (API scaffolded) |

---

## Phase Details

### Phase 1: Foundation & Data Pipeline ✅
**Goal**: Reproducible ingest → audit → split artifacts.  
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, ENG-01  
**Success Criteria**:
1. Nutrition5k audit detects corruption/missing assets
2. Official train/test split respected (dish_id boundary)
3. 5-fold stratified CV artifacts generated from code
4. Reproducible `data/splits/` directory

**Plans**: ✅ All complete
- [x] 01-01: Repo structure, tooling baseline
- [x] 01-02: Ingest, audit, subset selection, split generation
- [x] 01-03: CV fold artifacts, manifests, setup docs

---

### Phase 2: Foundation Preprocessing ✅
**Goal**: Initial RGB+Depth processing and FoodSAM legacy masking.  
**Requirements**: PREP-01, PREP-02, PREP-03, SEGM-01  
**Success Criteria**:
1. Each dish → `{dish_id}_rgb.pt` and `{dish_id}_depth.pt` saved
2. Pipeline is resumable
3. FoodSAM (SAM 1) masking implemented

**Plans**: ✅ All complete
- [x] 02-01: FoodSAM integration and wrapper
- [x] 02-02: Bilateral+CLAHE+TELEA+Gaussian preprocessing
- [x] 02-03: Artifact generation scripts

---

### Phase 3: SAM 2 -> GLPN -> ViT Pipeline 🔄
**Goal**: Implement the 3-stage accuracy pipeline for MVP.  
**Requirements**: PREP-04, SEGM-02, MODL-01, MODL-02  
**Success Criteria**:
1. `FoodSegmenterSAM2` generates high-quality masks
2. `DepthEstimatorGLPN` recovers 3D structure from 2D images
3. Composite images (RGB+Mask+Depth) generated for 10-dish MVP subset
4. ViT-based mass regressor trained and achieving MAE ≤ 40 kcal

**Plans**: 🔄 In progress
- [x] 03-01: Implement SAM 2 and GLPN model adapters
- [ ] 03-02: Composite image generation and preprocessing update
- [ ] 03-03: ViT regressor implementation and training

---

### Phase 4: Full Dataset Training Run ❌
**Goal**: Run the 3-stage pipeline through 5-fold CV on the full Nutrition5k dataset.  
**Requirements**: ENS-01, ENS-02, DATA-05, DATA-06  
**Success Criteria**:
1. All dishes preprocessed to `data/processed/features/`
2. 5-fold model checkpoints saved
3. Ensemble inference running at ≤ 200ms per image

---

### Phase 5: Evaluation & Verification ❌
**Goal**: Prove the model is accurate; detection of failure modes; complete verification layer.  
**Requirements**: EVAL-01, EVAL-02, EVAL-03, VERI-01, VERI-02, VERI-03  
**Success Criteria**:
1. Reports: MAE, MAPE, R², RMSE, Bias, Spearman — per model and ensemble
2. Constant-prediction failure mode detected explicitly
3. Tier 3 USDA cross-reference implemented
4. Targets: cal MAE ≤ 40 kcal; MAPE ≤ 12%; R² ≥ 0.85; Spearman ≥ 0.90

---

### Phase 6: FastAPI Delivery & Quality Hardening ✅ (scaffolded)
**Goal**: Async job/poll API; quality gates.  
**Requirements**: API-01, API-02, API-03, ENG-02  
**Success Criteria**:
1. `POST /predict` accepts image, returns `image_id` immediately
2. `GET /result/{image_id}` returns nutritional estimates + verification metadata
3. Response includes confidence and Gemini fallback note
4. Inference ≤ 200ms normal; ≤ 3s with Gemini fallback

---

## Active Constraints

| Constraint | Value |
|-----------|-------|
| GPU | RTX 3050 / 4GB VRAM |
| Model | SAM 2 + GLPN + ViT-B/16 |
| Target MAE | ≤ 40 kcal |
| Target MAPE | ≤ 12% |
| Target inference | ≤ 200ms (normal) / ≤ 3s (Gemini) |

---
*Roadmap updated: 2026-04-20 — 3-stage SAM 2 -> GLPN -> ViT pivot*
