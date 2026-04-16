# Roadmap: NutriSnap

## Overview

NutriSnap v1 builds a multi-layer accuracy pipeline: full RGB+Depth preprocessing, a three-model weighted ensemble (EfficientNetV2-B0 + ResNet101 + Multi-Task CNN with ingredient awareness), SAM-LoRA food segmentation, 5-fold stratified CV, and a 3-tier verification layer (rule-based → Gemini API → optional USDA). Target: calorie MAE ≤ 40 kcal on Nutrition5k at ≤ 200ms inference per image on an RTX 3050.

See [`misc/strategy_final_2026-04-16.md`](../misc/strategy_final_2026-04-16.md) for the complete blueprint.

---

## Phase Summary

| Phase | Name | Status |
|-------|------|--------|
| 1 | Foundation & Data Pipeline | ✅ Complete |
| 2 | Preprocessing & Segmentation | ✅ Complete |
| 3 | SAM LoRA Fine-Tuning | ❌ Pending |
| 4 | Nutrition Model & Ensemble | 🔄 In Progress (Model 1 done) |
| 5 | Full Dataset Training Run | ❌ Blocked (needs preprocessing) |
| 6 | Evaluation & Verification | ❌ Pending |
| 7 | FastAPI Delivery & Quality Hardening | ✅ Complete (API scaffolded) |

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

**Scripts**:
1. `scripts/ingest_nutrition5k.py` — builds `data/splits/dish_manifest.csv`
2. `scripts/audit_dataset.py` — validates raw data integrity
3. `scripts/generate_splits.py` — creates `data/splits/{train,val,test}_ids.txt`
4. `scripts/generate_folds.py` — creates `data/splits/cv_folds.json`

---

### Phase 2: Preprocessing & Segmentation ✅
**Goal**: Full RGB+Depth tensor pipeline; FoodSAM food masking.  
**Requirements**: PREP-01, PREP-02, PREP-03, SEGM-01  
**Success Criteria**:
1. Each dish → `{dish_id}_rgb.pt` (3,224,224) and `{dish_id}_depth.pt` (1,224,224) saved
2. Pipeline is resumable (skips existing files)
3. FoodSAM can generate food masks for representative samples

**Plans**: ✅ All complete
- [x] 02-01: FoodSAM integration and wrapper
- [x] 02-02: Bilateral+CLAHE+TELEA+Gaussian preprocessing
- [x] 02-03: Artifact generation scripts

**Script**:
5. `scripts/preprocess_full.py` — main preprocessing pipeline (~4 hours for 5k dishes)

---

### Phase 3: SAM LoRA Fine-Tuning ❌
**Goal**: Adapt SAM to food-specific segmentation using LoRA adapters.  
**Requirements**: PREP-04, SEGM-02  
**Success Criteria**:
1. LoRA adapters added to SAM ViT-B image encoder attention layers
2. Fine-tuned on Nutrition5k food masks
3. Binary masks applied to RGB+Depth; background → 0 before tensor save

**Plans**: ❌ Not yet planned
- [ ] 03-01: LoRA adapter implementation for SAM
- [ ] 03-02: Fine-tuning data preparation (mask loading from N5k)
- [ ] 03-03: Fine-tuned segmentation integrated into preprocess_full.py

---

### Phase 4: Nutrition Model & Ensemble 🔄
**Goal**: Three-model weighted ensemble (EfficientNetV2-B0 + ResNet101 + Multi-Task CNN).  
**Requirements**: MODL-01 through MODL-06, ENS-01, ENS-02  
**Success Criteria**:
1. Model 1 (EfficientNetV2-B0 + DepthCNN) trains with AMP within 4GB VRAM ✅
2. Model 2 (ResNet101) trained with identical head design
3. Model 3 (Multi-Task CNN + ingredient embedding from component_weights.tsv) implemented
4. All three trained via 5-fold stratified CV, best checkpoint per fold saved
5. Weighted ensemble inference: `weight_i = 1/MAE_i` normalized

**Plans**: 🔄 In progress
- [x] 04-01: Model 1 implementation (EfficientNetV2-B0 + DepthCNN dual-branch)
- [ ] 04-02: Model 2 (ResNet101 + same multi-task head)
- [ ] 04-03: Model 3 (Multi-Task CNN + ingredient embedding + task-specific heads)

---

### Phase 5: Full Dataset Training Run ❌
**Goal**: Run all three models through 5-fold CV on the full Nutrition5k dataset.  
**Requirements**: ENS-01, ENS-02, DATA-05, DATA-06  
**Blocked by**: Phase 2 preprocessing must complete for all dishes; Phase 3 (SAM-LoRA) preferred but not required for initial run  
**Success Criteria**:
1. All dishes preprocessed to `data/processed/features/`
2. 5×3 model checkpoints saved in `models/checkpoints/`
3. Ensemble inference running at ≤ 200ms per image

**Scripts**:
6. `src/train.py` — main training entrypoint
   ```
   .venv\Scripts\python.exe src/train.py --config configs/experiment/ensemble_5fold.yaml
   ```

---

### Phase 6: Evaluation & Verification ❌
**Goal**: Prove the model is accurate; detection of failure modes; complete verification layer.  
**Requirements**: EVAL-01, EVAL-02, EVAL-03, VERI-01, VERI-02, VERI-03  
**Success Criteria**:
1. Reports: MAE, MAPE, R², RMSE, Bias, Spearman, ensemble std dev — per model and ensemble
2. Constant-prediction failure mode detected explicitly
3. Tier 3 USDA cross-reference implemented
4. Targets: cal MAE ≤ 40 kcal; MAPE ≤ 12%; R² ≥ 0.85; Spearman ≥ 0.90

**Scripts**:
7. `scripts/evaluate_ensemble.py` — evaluation report
8. `scripts/smoke_check_pipeline.py` — end-to-end sanity check

---

### Phase 7: FastAPI Delivery & Quality Hardening ✅ (scaffolded)
**Goal**: Async job/poll API; quality gates.  
**Requirements**: API-01, API-02, API-03, ENG-02  
**Success Criteria**:
1. `POST /predict` accepts image, returns `image_id` immediately
2. `GET /result/{image_id}` returns nutritional estimates + verification metadata
3. Response includes confidence (High/Medium/Low) and Gemini fallback note if used
4. Inference ≤ 200ms normal; ≤ 3s with Gemini fallback

---

## Active Constraints

| Constraint | Value |
|-----------|-------|
| GPU | RTX 3050 / 4GB VRAM |
| Batch | 8 with grad_accum=4 → effective 32 |
| AMP | FP16 enabled |
| Preprocessing rate | ~15 dishes/sec on CPU |
| Target MAE | ≤ 40 kcal |
| Target MAPE | ≤ 12% |
| Target inference | ≤ 200ms (normal) / ≤ 3s (Gemini) |

---
*Roadmap defined: 2026-04-11*  
*Last updated: 2026-04-16 — Final architecture revision (3-model ensemble, SAM-LoRA, 3-tier verification)*
