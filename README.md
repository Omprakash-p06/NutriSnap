# NutriSnap

> **Estimate calories, protein, carbs, and fats from a single meal photo.**  
> Accuracy-driven MVP: 10 visually-distinct dishes → MAE ≤ 40 kcal → then scale.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-orange)](https://pytorch.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-async%20API-green)](https://fastapi.tiangolo.com)

---

## Architecture

```
📷 Single Meal Photo
       ↓
┌─ Preprocessing ──────────────────────────────────────────────────────┐
│  RGB:   Bilateral → CLAHE → ImageNet Normalize → 224×224            │
│  Depth: 16-bit→m → Median → TELEA Inpaint → Normalize → 224×224    │
│  Segm:  SAM + LoRA (food-tuned) → Binary Mask → apply to RGB+Depth  │
│  Aug:   Rotation, Flip, Crop, Color Jitter, Blur, Dropout (online)  │
└──────────────────────────────────────────────────────────────────────┘
       ↓
┌─ 3-Model Weighted Ensemble (5-Fold Stratified CV) ───────────────────┐
│  Model 1 (Primary):   EfficientNetV2-B0 + DepthCNN                  │
│  Model 2 (Secondary): ResNet101 (different inductive bias)           │
│  Model 3 (Tertiary):  Multi-Task CNN + Ingredient Embedding          │
│  Aggregation: weight_i = 1/MAE_i per fold (auto-calibrated)         │
└──────────────────────────────────────────────────────────────────────┘
       ↓
┌─ 3-Tier Verification ────────────────────────────────────────────────┐
│  Tier 1: Rule validator → bounds, macro-cal check, vol, std dev     │
│  Tier 2: Gemini 2.0 Flash API (if Tier 1 flags anything)            │
│  Tier 3: USDA FoodData cross-ref (optional)                          │
└──────────────────────────────────────────────────────────────────────┘
       ↓
✅  FastAPI: POST /predict → GET /result/{image_id}
    calories · protein · carbs · fats · confidence · verification note
```

**Architecture doc**: [misc/strategy_final_2026-04-16.md](misc/strategy_final_2026-04-16.md)  
**Pipeline diagram**: [misc/nutrisnap_pipeline_2026-04-16.svg](misc/nutrisnap_pipeline_2026-04-16.svg)

---

## MVP Scope: 10 Dishes

The v1.0 MVP trains only on 10 visually-distinct dish types:

| Pizza | Salad | Pasta | Rice Bowl | Sandwich |
|-------|-------|-------|-----------|----------|
| Soup | Stir-fry | Omelette | Smoothie | Grilled Chicken |

**Why 10?** Prove the methodology hits MAE ≤ 40 kcal first. Once validated, run `prepare_data.py` without `--mvp-only` to scale the same pipeline to all ~5k Nutrition5k dishes. No architectural changes needed.

---

## Target Metrics (MVP)

| Metric | Target |
|--------|--------|
| Calorie MAE | ≤ 40 kcal |
| Calorie MAPE | ≤ 12% |
| R² | ≥ 0.85 |
| Spearman | ≥ 0.90 |
| Ensemble std dev | ≤ 50 kcal |
| Inference (normal) | < 200 ms |
| Inference (Gemini fallback) | 1–3 s |

---

## 🚀 Getting Started (Step-by-Step)

Follow these steps in order to set up NutriSnap and run the 10-dish MVP pipeline.

### Step 1 — Prerequisites & environment
1. **Hardware**: Ensure you have an NVIDIA GPU (RTX 3050+ recommended).
2. **Setup Environment**:
   ```powershell
   # Always run this once per session on Windows
   $env:PYTHONUTF8=1

   python -m venv .venv
   .venv\Scripts\activate
   pip install -e .
   ```

### Step 2 — Download the Dataset
1. Download the [Nutrition5k dataset](https://www.kaggle.com/datasets/gillesokhin/nutrition5k-dataset) from Kaggle.
2. Extract the archive into the project root.
3. **Verify Paths**: Ensure the following folder exists:
   `data/raw/archive (4)/imagery/realsense_overhead/`

---

### Step 3 — FoodSAM Weights (~2.4 GB)
Downloads the Segment Anything model weights required for background masking.
```powershell
.venv\Scripts\python.exe scripts/setup_foodsam.py
```

### Step 4 — Ingest & Index
Normalizes the raw CSV data and builds the initial `dishes.csv` manifest.
```powershell
.venv\Scripts\python.exe scripts/ingest_nutrition5k.py
```

### Step 5 — Audit, Splits & CV
Performs Phase 1.2 (mass consistency) and Phase 1.3 (blur audit). Generates the 5-fold stratified CV splits for the 10-dish MVP.
```powershell
.venv\Scripts\python.exe scripts/prepare_data.py --mvp-only
```

### Step 6 — Preprocess Tensors
Generates pre-masked RGB and Depth tensors. For the 10-dish MVP, this takes ~5 minutes.
```powershell
.venv\Scripts\python.exe scripts/preprocess_full.py `
    --ids-file data/splits/mvp_subset_ids.txt `
    --output-dir data/processed/features
```

### Step 7 — Train the Ensemble
Trains the 3-model weighted ensemble.
```powershell
# Optional: verify with a dry run (1 epoch)
.venv\Scripts\python.exe src/train.py --config configs/experiment/ensemble_5fold.yaml --limit 10 --epochs 1

# Start full training
.venv\Scripts\python.exe src/train.py --config configs/experiment/ensemble_5fold.yaml
```

### Step 8 — Evaluation
Computes finalized metrics (MAE, MAPE, R²) and generates the evaluation report.
```powershell
.venv\Scripts\python.exe scripts/verify_results.py
```

### Step 9 — Start the API
Launches the FastAPI backend for real-time predictions.
```powershell
.venv\Scripts\uvicorn nutrisnap.api.main:app --host 0.0.0.0 --port 8000
```

---

## Scripts Reference

| Script | Step | Purpose |
|--------|------|---------|
| `scripts/setup_foodsam.py` | 1 | Download FoodSAM weights (once) |
| `scripts/ingest_nutrition5k.py` | 2 | Build `data/interim/dishes.csv` |
| `scripts/prepare_data.py` | 3 | Audit + splits + 5-fold CV |
| `scripts/preprocess_full.py` | 4 | RGB+Depth tensor pipeline |
| `src/train.py` | 5+6 | Dry run + full ensemble training |
| `scripts/verify_results.py` | 7 | Evaluate metrics + smoke check |
| `scripts/evaluate_diagnostics.py` | Optional | Deep failure-mode diagnostics |

---

## Scaling to Full Dataset

After the 10-dish MVP hits MAE ≤ 40 kcal:

```powershell
# 1. Generate full splits
.venv\Scripts\python.exe scripts/prepare_data.py   # no --mvp-only flag

# 2. Preprocess all ~5k dishes (~3.5 hours on CPU, resumable)
.venv\Scripts\python.exe scripts/preprocess_full.py --ids-file data/splits/train_ids.txt --output-dir data/processed/features
.venv\Scripts\python.exe scripts/preprocess_full.py --ids-file data/splits/val_ids.txt   --output-dir data/processed/features
.venv\Scripts\python.exe scripts/preprocess_full.py --ids-file data/splits/test_ids.txt  --output-dir data/processed/features

# 3. Train (same command, same config)
.venv\Scripts\python.exe src/train.py --config configs/experiment/ensemble_5fold.yaml
```

---

## Project Structure

```
NutriSnap/
├── configs/
│   ├── data/data_config.yaml          # paths, mvp_dish_count: 10, split fractions
│   ├── models/efficientnet_v2_b0.yaml # model architecture
│   └── experiment/ensemble_5fold.yaml # training hyperparameters
├── data/
│   ├── raw/                           # Nutrition5k — never modify
│   ├── interim/dishes.csv             # validated dish manifest
│   ├── processed/features/            # {dish_id}_rgb.pt + _depth.pt
│   └── splits/                        # IDs, cv_folds.json, fold txts
├── misc/
│   ├── strategy_final_2026-04-16.md   # ← Definitive blueprint
│   └── nutrisnap_pipeline_2026-04-16.svg
├── models/checkpoints/                # best_fold_N.pth
├── reports/                           # evaluation_results.json
├── scripts/                           # 6 pipeline scripts
└── src/
    ├── train.py
    └── nutrisnap/
        ├── api/                       # FastAPI endpoints
        ├── data/                      # dataset, augmentation
        ├── models/                    # backbone, depth_cnn, regressor, loss, heads
        ├── pipeline/                  # FoodSAM segmenter
        ├── training/                  # 3-phase trainer
        └── verification/              # rule_validator, api_fallback
```

---

## Hardware Notes

| Item | Value |
|------|-------|
| Minimum GPU | RTX 3050 / 4GB VRAM |
| Training VRAM | ~3.2 GB (batch=8, AMP FP16, grad_accum=4) |
| MVP preprocessing (10 dishes) | < 5 minutes on CPU |
| Full dataset preprocessing | ~3.5 hours on CPU (resumable) |
| Normal inference | < 200 ms |
| Gemini fallback | 1–3 s |