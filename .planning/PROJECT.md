# NutriSnap

## What This Is

NutriSnap is a production-oriented AI system that estimates calories, protein, carbohydrates, and fats from a single meal photo. The v1.0 MVP focuses on **10 visually-distinct dish types** (Pizza, Salad, Pasta, Rice Bowl, Sandwich, Soup, Stir-fry, Omelette, Smoothie, Grilled Chicken) to prove the methodology and hit accuracy targets before scaling to the full Nutrition5k dataset.

The pipeline uses a three-model weighted ensemble (EfficientNetV2-B0, ResNet101, Multi-Task CNN), SAM-LoRA food segmentation, full RGB+Depth preprocessing, and a 3-tier verification layer (rule-based → Gemini 2.0 Flash → optional USDA).

The definitive architecture is in `misc/strategy_final_2026-04-16.md`.

## Core Value

A user can upload a single meal image and receive a realistic, verified nutrition estimate quickly enough for real-world use on commodity hardware (RTX 3050 / 4GB VRAM).

## Requirements

### Validated

- [x] Data pipeline (ingest → splits → 5-fold CV) is reproducible
- [x] Full RGB + Depth preprocessing pipeline implemented (Bilateral + CLAHE + TELEA inpainting + Gaussian)
- [x] FoodSAM segmentation integrated
- [x] EfficientNetV2-B0 dual-branch model (RGB + DepthCNN) implemented and training verified on CUDA
- [x] Uncertainty-weighted multi-task loss (Kendall et al.) implemented
- [x] 3-phase transfer learning + cosine LR scheduler implemented
- [x] Rule-based validator fully implemented (bounds + calorie-macro consistency + volume check)
- [x] Gemini 2.0 Flash API fallback implemented (graceful no-op without key)
- [x] FastAPI async `/predict` + `/result/{image_id}` endpoints implemented

### Active

- [ ] SAM LoRA fine-tuning on Nutrition5k food masks
- [ ] ResNet101 secondary model (Model 2) implementation
- [ ] Multi-Task CNN + ingredient embedding model (Model 3) implementation
- [ ] Ingredient-mass correction pipeline (`component_weights.tsv`)
- [ ] Frame filtering from 360° video
- [ ] Full 5-fold training run across all ~5k dishes
- [ ] Weighted ensemble inference (weight = 1/MAE per fold)
- [ ] Evaluation report: MAE, MAPE, R², RMSE, Bias, Spearman, std dev

## Out of Scope

- Native mobile or full consumer frontend before the backend MVP is validated
- Full 5k-dish training before the 10-dish MVP hits its accuracy targets (MAE ≤ 40 kcal)
- Cloud-GPU-only deployment — must remain viable on local 4GB hardware
- Barcode scanning or manual entry — visual estimation from a single image is the differentiator

## Context

The architecture uses three complementary models:
1. **EfficientNetV2-B0 (Primary)** — RGB 224×224 → 1,280-dim features + DepthCNN → 64-dim + channel-spatial attention fusion
2. **ResNet101 (Secondary)** — RGB 224×224, different inductive bias for ensemble diversity
3. **Multi-Task CNN + Ingredient Embedding (Tertiary)** — RGB + Depth + ingredient embedding from `component_weights.tsv`

All three trained via 5-fold stratified cross-validation (stratified by calorie bins, grouped by `dish_id`). Predictions aggregated via `weight_i = 1/MAE_i` weighted ensemble.

Verification follows a 3-tier cascade:
- **Tier 1** (always): Rule-based bounds + calorie-macro consistency + volume check + ensemble std dev
- **Tier 2** (if flagged): Gemini 2.0 Flash two-step prompt
- **Tier 3** (optional): USDA FoodData Central cross-reference

## Constraints

- **Hardware**: RTX 3050 / 4GB VRAM — all training and inference must stay within this budget
- **Performance**: Inference ≤ 2 seconds (normal path); ≤ 3 seconds (Gemini fallback path)
- **Accuracy**: Calorie MAE ≤ 40 kcal; Calorie MAPE ≤ 12%; R² ≥ 0.85; Spearman ≥ 0.90
- **Architecture**: Transparent modular pipeline — each stage is independently testable and replaceable
- **Deployment**: Production FastAPI backend with async job/poll pattern

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Three-model weighted ensemble (EfficientNetV2-B0 + ResNet101 + Multi-Task) | Diversity between architectures reduces ensemble error; weighted by 1/MAE provides automatic calibration | Active |
| SAM LoRA fine-tuning instead of generic SAM | Generic SAM underperforms on food; LoRA adapts it with minimal extra parameters | Active |
| Uncertainty-weighted multi-task loss (Kendall et al.) | Automatically balances gradient contributions across 4 nutrient tasks without manual tuning | Implemented |
| Ingredient-mass correction (5% tolerance) | Research shows 6–42% improvement in prediction metrics | Active |
| 3-tier verification (rules → Gemini → USDA) | Catches different failure modes: hard bounds, AI review, ground truth cross-reference | Implemented (Tier 1+2); Tier 3 optional |
| TELEA inpainting for depth maps | Fills missing depth pixels without corrupting geometric structure | Implemented |
| Stratified 5-fold CV by calorie bins | Ensures balanced calorie distribution across folds, preventing training/validation skew | Active |

---
*Last updated: 2026-04-16 — Final strategic architecture locked (see misc/strategy_final_2026-04-16.md)*
