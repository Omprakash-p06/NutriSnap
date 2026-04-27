# NutriSnap Pipeline Guide

This guide outlines the standard workflow for training and verifying the NutriSnap nutrition estimation system.

## Workflow Overview

The pipeline consists of six main stages: Setup, Ingestion, Preparation, Preprocessing, Training, and Verification.

### 0. Model Setup
Downloads necessary model weights (e.g., SAM).
```powershell
python scripts/setup_foodsam.py
```

### 1. Data Ingestion
Normalizes the raw Nutrition5k CSV files into a consistent internal format.
```powershell
python scripts/ingest_nutrition5k.py
```
*Output*: `datasets/interim/dishes.csv`

### 2. Dataset Preparation
Audits the raw imagery (checks for blur and mass consistency), splits dishes into Train/Val/Test sets, and generates 5-fold cross-validation splits.
```powershell
# For a quick MVP run (10 dishes):
python scripts/prepare_data.py --mvp-only

# For a full dataset run:
python scripts/prepare_data.py
```
*Output*: `datasets/splits/`, `datasets/interim/dishes.csv`

### 3. Full Preprocessing
Runs the complete RGB and Depth processing chains, including bilateral filtering, CLAHE, and **SAM-LoRA background masking**.
```powershell
# MVP Preprocessing (recommended first step):
python scripts/preprocess_full.py --ids-file datasets/splits/mvp_subset_ids.txt

# Full Dataset Preprocessing:
python scripts/preprocess_full.py --ids-file datasets/splits/train_ids.txt
```
*Output*: `datasets/processed/features/*.pt`

### 4. Volume Feature Extraction
Computes volume and area from preprocessed depth maps.
```powershell
python scripts/generate_volume_features.py
```
*Output*: `datasets/processed/features/volume_features.csv`

### 5. Training (5-Fold CV)
Executes the Three-Phase transfer learning protocol (Heads → Partial Backbone → Full Fine-tune) across all 5 folds.
```powershell
# MVP Subset Training:
python src/train.py --config configs/experiment/ensemble_mvp.yaml

# Full Training:
python src/train.py --config configs/experiment/ensemble_5fold.yaml
```
*Output*: `checkpoints/`

### 6. Verification & Evaluation
Computes ensemble metrics (MAE, MAPE, R², Spearman) on the test set and performs an end-to-end "smoke check" on a validation sample.
```powershell
python scripts/verify_results.py --config configs/experiment/ensemble_mvp.yaml
```
*Output*: `reports/evaluation_results.json`

---

## Hardware Targets
- **GPU**: NVIDIA GTX 1650 (4GB VRAM) or better.
- **VRAM Management**: SAM segmentation is processed dish-by-dish with automatic VRAM unloading to stay within the 4GB limit.
