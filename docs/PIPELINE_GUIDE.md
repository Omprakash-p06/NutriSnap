# NutriSnap Pipeline Guide

This guide outlines the standard workflow for training and verifying the NutriSnap nutrition estimation system.

## Workflow Overview

The pipeline consists of five main stages: Ingestion, Preparation, Preprocessing, Training, and Verification.

### 1. Data Ingestion
Normalizes the raw Nutrition5k CSV files into a consistent internal format.
```bash
python scripts/ingest_nutrition5k.py
```
*Output*: `data/interim/dishes.csv`

### 2. Dataset Preparation
Audits the raw imagery (checks for blur and mass consistency), splits dishes into Train/Val/Test sets, and generates 5-fold cross-validation splits.
```bash
# For a full dataset run:
python scripts/prepare_data.py

# For a quick MVP run (10 dishes):
python scripts/prepare_data.py --mvp-only
```
*Output*: `data/splits/`, `data/interim/dishes.csv`

### 3. Full Preprocessing
Runs the complete RGB and Depth processing chains, including bilateral filtering, CLAHE, and **SAM-LoRA background masking**.
```bash
# MVP Preprocessing (recommended first step):
python scripts/preprocess_full.py --ids-file data/splits/mvp_subset_ids.txt

# Full Dataset Preprocessing:
python scripts/preprocess_full.py --ids-file data/splits/train_ids.txt
```
*Output*: `data/processed/features/*.pt`

### 4. Training (5-Fold CV)
Executes the Three-Phase transfer learning protocol (Heads → Partial Backbone → Full Fine-tune) across all 5 folds.
```bash
python src/train.py --config configs/experiment/ensemble_5fold.yaml
```
*Output*: `models/checkpoints/ensemble_v2/`

### 5. Verification & Evaluation
Computes ensemble metrics (MAE, MAPE, R²) on the test set and performs an end-to-end "smoke check" on a validation sample.
```bash
python scripts/verify_results.py
```
*Output*: `reports/evaluation_results.json`

---

## Hardware Targets
- **GPU**: NVIDIA GTX 1650 (4GB VRAM) or better.
- **VRAM Management**: SAM segmentation is processed dish-by-dish with automatic VRAM unloading to stay within the 4GB limit.
