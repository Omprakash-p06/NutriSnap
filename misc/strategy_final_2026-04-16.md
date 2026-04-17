# NutriSnap: Final Implementation Strategy (MVP v1.1)

> **Last updated:** 2026-04-17
> **Change from v1.0:** Added Swin Transformer backbone path, ingredient-mass correction, R²/Spearman metrics, and clarified segmentation/depth architecture per AGENTS.md constraints.

This document is the definitive source of truth for the NutriSnap MVP implementation. It incorporates the research finding that **Swin Transformer-based architectures achieve the highest accuracy on Nutrition5k**, a multi-stage pipeline for portion estimation, and a 4-tier verification protocol designed for 4GB-GPU hardware.

---

## 📊 1. Dataset Scale & Splits

- **Core Pivot**: Multi-view sampling from 360° side-angle videos (Cameras A, B, C, D).
- **MVP Selection**: Top 10 "High-Density" dishes by frame count (saved in `mvp_subset_ids.txt`).
- **Capacity**: ~5,100 high-quality images (capped at 500 frames per dish for balance).
- **Splitting**: **Strictly by Dish ID** (`GroupShuffleSplit`) to prevent cross-frame leakage across Train, Val, and Test sets. Leakage assertion is enforced in `splitter.py`.
- **MVP Hold-out**: 15% dishes reserved for final unbiased testing via `generate_train_test_split()`; 5-fold CV on remaining 85%.

| Metric       | Target    |
|--------------|-----------|
| Calorie MAE  | ≤ 40 kcal |
| Calorie MAPE | ≤ 12%     |
| R²           | ≥ 0.85    |
| Spearman ρ   | ≥ 0.80    |

---

## 🛠️ 2. Architectural Blueprint

### 2.1 Preprocessing (CPU + GPU)

- **RGB**: Resize (224), ImageNet normalization, Bilateral filtering, CLAHE (in `preprocessing.py`).
- **Depth (Overhead)**: 16-bit-to-meter conversion, median noise reduction, morphological closing, TELEA inpainting, Gaussian smoothing, clip-normalize to [0, 1].
- **Depth (Side Views)**: Zero-tensor placeholder; geometry handled by `ChannelAttentionFusion` which auto-down-weights missing depth signals.
- **Masking**: `apply_mask()` in `preprocessing.py` zeros non-food pixels (supports FoodSAM mask input when available).
- **Ingredient-Mass Correction**: `apply_ingredient_mass_correction()` in `preprocessing.py` re-scales per-ingredient masses to the measured dish total, eliminating systematic mass-mismatch error. **Shown to substantially reduce calorie MAE.**

### 2.2 Segmentation Stage (FoodSAM — planned)

Per `AGENTS.md` architecture: **FoodSAM** (food-tuned SAM variant) is the target segmentation model for background suppression. The `apply_mask()` utility is already wired for mask input. FoodSAM integration is pending as a dedicated phase.

> ⚠️ Note: General SAM 2 was evaluated as an alternative but **FoodSAM** is preferred per AGENTS.md because it is specifically tuned on food imagery and avoids the overhead of prompting a general segmentation model.

### 2.3 Depth Estimation Path (FoodVolume — planned)

Per `AGENTS.md` architecture: **FoodVolume** is the preferred MVP volume-estimation path for the 4GB hardware target. VolETA is kept as a benchmark/reference path only. GLPN (Global-Local Path Network) monocular depth was evaluated but the raw RGBD overhead-camera depth available in Nutrition5k is already high quality and avoids an extra inference pass within the latency budget.

### 2.4 Backbone Options (Active)

| Backbone | Output Dim | VRAM | Notes |
|---|---|---|---|
| **EfficientNetV2-B0** ✅ | 1280 | ~1.2 GB | Current default. Best efficiency/performance. |
| **Swin Transformer Tiny** ✅ | 768 | ~1.8 GB | **Highest accuracy on Nutrition5k** per research. Long-range spatial attention captures plate geometry. Use `ensemble_5fold_swin.yaml`. |
| **ResNet-101** ✅ | 2048 | ~2.1 GB | Classic baseline for ensemble diversity. |

All three are implemented in `src/nutrisnap/models/backbone.py` and selectable via the `model.backbone` config key.

### 2.5 Fusion & Attention

- **RGB-D Fusion**: RGB Backbone + `DepthCNN` (3-layer lightweight CNN, 64-dim output).
- **ChannelAttentionFusion** (`fusion.py`): Channel-wise attention weights modalities based on global context. Zero-depth side views are automatically down-weighted.
- **Multi-Task Heads** (`heads.py`): Separate regression heads for calories, fat, carbs, protein.
- **Loss**: `UncertaintyWeightedLoss` — Kendall et al. (2018) learnable homoscedastic uncertainty weighting. Automatically balances the 4 tasks without manual loss weight tuning.

### 2.6 Ensemble Strategy

- **Weighted Averaging**: 5-fold ensemble using `1/MAE` weights for final inference.
- **Backbone Mix**: EfficientNetV2-B0 + Swin-Tiny diversity (replaces EfficientNet + ResNet101).

---

## ⚙️ 3. Training Configuration

### 3-Phase Transfer Learning

| Phase | Epochs | Strategy |
|---|---|---|
| 1 | 0 → `phase1_epochs` | Backbone frozen, train heads only |
| 2 | `phase1` → `phase2_epochs` | Last 3 backbone layers/stages unfrozen |
| 3 | `phase2` → `max_epochs` | Full backbone fine-tuning |

### LR Schedule
- **Warmup**: 5-epoch `LinearLR` (start_factor=0.1) to stabilize early training.
- **Cosine Annealing**: `CosineAnnealingLR` for remaining epochs (`eta_min=1e-7`).

### Other Optimizations
- **Gradient clipping**: `max_norm=1.0` (prevents exploding gradients).
- **Mixed precision (AMP)**: Full CUDA AMP on GTX 1650.
- **Gradient accumulation**: `grad_accum_steps=4` → effective batch size 32.
- **Early stopping**: Patience-based on validation loss.

---

## 📈 4. Evaluation Metrics

All metrics computed per-nutrient `[calories, fat, carbs, protein]` in `trainer.validate()`:

| Metric | Purpose | Target (calories) |
|---|---|---|
| **MAE** | Absolute error in real units | ≤ 40 kcal |
| **MAPE** | Relative error (%) | ≤ 12% |
| **R²** | Variance explained | ≥ 0.85 |
| **Spearman ρ** | Ranking/ordering ability | ≥ 0.80 |
| Std Dev | Prediction spread | — |

> R² and Spearman are now implemented in `trainer.py` and included in checkpoint metadata.

---

## ✅ 5. Four-Layer Verification Strategy

Every prediction passes through a cascading verification loop:

1. **Rule-Based Validator**: Hard bounds (50–1500 kcal) + Macro-calorie consistency checks (< 20% error).
2. **Gemini Flash API (LLM)**: Triggered on rule violation or high ensemble variance. Provides visual "sanity check" correction.
3. **USDA Cross-Reference**: Automated comparison of AI estimates vs. USDA FoodData Central reference values.
4. **Human Flag**: Final escalation for extreme outliers that fail Layers 2 + 3.

---

## 🚀 6. Execution Workflow

### Step 1: Data Preparation
```powershell
# Run preprocessing + generate all splits
.venv\Scripts\python.exe scripts/generate_splits.py --config configs/data/data_config.yaml
```

### Step 2: Training

**EfficientNetV2-B0 (current default — fastest):**
```powershell
.venv\Scripts\python.exe src/train.py --config configs/experiment/ensemble_5fold.yaml
```

**Swin Transformer Tiny (highest accuracy):**
```powershell
.venv\Scripts\python.exe src/train.py --config configs/experiment/ensemble_5fold_swin.yaml
```

**Quick dry-run (smoke test, 20 samples, 1 epoch):**
```powershell
.venv\Scripts\python.exe src/train.py --config configs/experiment/ensemble_5fold.yaml --limit 20 --epochs 1
```

### Step 3: Deployment
```powershell
.venv\Scripts\uvicorn nutrisnap.api.main:app --host 0.0.0.0 --port 8000
```

---

## 📋 7. Gap Status (from v1.0 audit)

| Component | v1.0 | v1.1 |
|---|---|---|
| EfficientNetV2-B0 backbone | ✅ | ✅ |
| Swin Transformer backbone | ❌ | ✅ Added |
| Depth branch (DepthCNN) | ✅ | ✅ |
| FoodSAM segmentation | ❌ | ⏳ Planned phase |
| FoodVolume depth (GLPN) | ❌ | ⏳ Planned phase |
| Ingredient-mass correction | ❌ | ✅ Added |
| MAE / MAPE metrics | ✅ | ✅ |
| R² metric | ❌ | ✅ Added |
| Spearman ρ metric | ❌ | ✅ Added |
| Warmup LR schedule | ✅ | ✅ |
| Cosine Annealing | ✅ | ✅ |
| Gradient clipping | ✅ | ✅ |
| 3-phase transfer learning | ✅ | ✅ |
| Dish-level leakage-safe split | ✅ | ✅ |
| Hold-out test set | ✅ | ✅ |
| 5-Fold CV | ✅ | ✅ |
| Geometric augmentations | ✅ | ✅ |
| CoarseDropout | ✅ | ✅ |
| DiffAugment | ❌ | 🔵 Backlog |
| Perceptual Loss (LPIPS) | ❌ | 🔵 Backlog |
| One-Cycle Policy | ❌ | 🔵 Deferred (Warmup→Cosine preferred) |
