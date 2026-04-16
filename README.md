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

## Setup

### Prerequisites
- Python 3.10+
- CUDA GPU (RTX 3050 / 4GB VRAM minimum)
- [Nutrition5k dataset](https://www.kaggle.com/datasets/gillesokhin/nutrition5k-dataset) extracted to `data/raw/archive (4)/`

### Install
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

### Set Gemini API Key (optional — for Tier 2 fallback)
```powershell
$env:GEMINI_API_KEY = "your_key_here"
```

---

## ▶ Run the Pipeline (Step by Step)

> **Always run `$env:PYTHONUTF8=1` first on Windows.**

### Step 1 — FoodSAM Setup (one-time, ~2.4 GB download)
```powershell
$env:PYTHONUTF8=1
.venv\Scripts\python.exe scripts/setup_foodsam.py
```

---

### Step 2 — Index the Dataset
```powershell
$env:PYTHONUTF8=1
.venv\Scripts\python.exe scripts/ingest_nutrition5k.py
```
Reads `dish_nutrition_values.csv`, normalises columns, deduplicates.  
**Output**: `data/interim/dishes.csv`

---

### Step 3 — Audit + Splits + 5-Fold CV (all in one script)
```powershell
$env:PYTHONUTF8=1
.venv\Scripts\python.exe scripts/prepare_data.py --mvp-only
```
`--mvp-only` limits everything to the 10-dish subset. Drop the flag to use the full dataset.

**What it does, in order:**
1. **Audit**: checks every dish has an RGB, depth file, and a nutrition row
2. **Ingredient-mass correction**: flags dishes where `|sum(ingredients) - total| > 5%`
3. **Trail split**: uses official `dish_ids/splits/test_ids.txt` boundary for test set; random 15% val from the remaining 85%
4. **5-fold CV**: stratified by calorie bins (quantile-based), grouped by dish_id so no frame leakage

**Output**:
- `data/interim/dishes.csv` — validated manifest
- `data/splits/train_ids.txt` / `val_ids.txt` / `test_ids.txt`
- `data/splits/cv_folds.json` — 5 folds, each with `train` and `val` dish_id lists
- `data/splits/train_fold_N.txt` / `val_fold_N.txt` (N=0..4)
- `data/splits/mvp_subset_ids.txt` — the 10 selected dish IDs

**How stratification works**: Calorie values grouped into 5 quantile bins (Very Low to Very High). Each bin distributed round-robin across folds. Every fold gets dishes from all calorie ranges — prevents "this fold only has light salads" skew.

---

### Step 4 — Preprocess RGB + Depth Tensors

For the 10-dish MVP this takes **minutes**, not hours.

```powershell
$env:PYTHONUTF8=1
.venv\Scripts\python.exe scripts/preprocess_full.py `
    --ids-file data/splits/mvp_subset_ids.txt `
    --output-dir data/processed/features
```

Each dish → `{dish_id}_rgb.pt` (3,224,224 float32) + `{dish_id}_depth.pt` (1,224,224 float32).  
Script is **resumable** — safe to interrupt and restart.

> **Full dataset later**: swap `--ids-file data/splits/train_ids.txt` (and repeat for val + test).

---

### Step 5 — Dry Run (GPU + Data Pipeline Check)
Before committing to full training, verify everything runs:
```powershell
$env:PYTHONUTF8=1
.venv\Scripts\python.exe src/train.py `
    --config configs/experiment/ensemble_5fold.yaml `
    --limit 10 --epochs 1
```
Should complete in < 2 minutes. If no CUDA/OOM errors → ready for full training.

---

### Step 6 — Train the Ensemble
```powershell
$env:PYTHONUTF8=1
.venv\Scripts\python.exe src/train.py --config configs/experiment/ensemble_5fold.yaml
```

Training schedule (per model, per fold):
- **Epochs 1–10**: backbone frozen, train heads only
- **Epochs 11–20**: unfreeze last 3 backbone layers (LR 1e-5)
- **Epochs 21+**: full backbone unfrozen (LR 1e-6)

**Output**: `models/checkpoints/ensemble_5fold_v1/best_fold_{0..4}.pth`

> Batch=8, grad_accum=4 → effective batch 32 with AMP FP16. Fits RTX 3050 4GB.

---

### Step 7 — Evaluate + Smoke Check (all in one)
```powershell
$env:PYTHONUTF8=1
.venv\Scripts\python.exe scripts/verify_results.py

# Run one stage only:
.venv\Scripts\python.exe scripts/verify_results.py --stage eval   # metrics
.venv\Scripts\python.exe scripts/verify_results.py --stage smoke  # end-to-end
```

Prints and saves MAE, MAPE, R², RMSE, Bias, Spearman, std dev for all 4 nutrients.  
Also checks: constant-prediction failure mode (std dev < 10 kcal = warning).  
**Output**: `reports/evaluation_results.json`

---

### Step 8 — Start the API
```powershell
$env:PYTHONUTF8=1
.venv\Scripts\uvicorn nutrisnap.api.main:app --host 0.0.0.0 --port 8000
```

```powershell
# Submit a meal photo
Invoke-RestMethod -Uri "http://localhost:8000/predict" -Method Post `
    -Form @{ file = Get-Item "meal.jpg" }
# → { "image_id": "abc123", "status": "accepted" }

# Poll for result
Invoke-RestMethod -Uri "http://localhost:8000/result/abc123"
# → { "calories": 450, "protein": 32, "carbs": 48, "fat": 12,
#     "confidence": "High", "verified": true }
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