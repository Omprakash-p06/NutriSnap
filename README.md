# NutriSnap 🍱

**AI-powered nutrition estimation from a single meal photo.**

NutriSnap is a production-oriented FastAPI backend that estimates **calories, protein, carbohydrates, and fats** from a single meal image using a transparent, modular deep-learning pipeline. Designed to run on commodity hardware (GTX 1650, 4 GB VRAM) with end-to-end inference under 2 seconds.

---

## 🏗️ Architecture Overview

NutriSnap uses a **multi-stage, 3D-aware pipeline** to directly tackle the core challenge of portion estimation:

```
Image → [Segmentation] → [Depth Branch] → [RGB + Depth Fusion] → [Nutrition Heads]
           FoodSAM         DepthCNN            Attention Fusion      [cal, fat, carb, prot]
         (planned)      (Swin Tiny or
                         EfficientNet)
```

### Backbone Options

| Backbone | Notes | Config |
|---|---|---|
| **Swin Transformer Tiny** | Highest accuracy on Nutrition5k | `configs/models/swin_tiny.yaml` |
| **EfficientNetV2-B0** | Best efficiency/speed (default) | `configs/models/efficientnet_v2_b0.yaml` |
| **ResNet-101** | Classic baseline, ensemble diversity | — |

### Key Components

| Module | Location | Purpose |
|---|---|---|
| `NutritionRegressor` | `src/nutrisnap/models/nutrition_regressor.py` | Main dual-branch model |
| `SwinTinyBackbone` | `src/nutrisnap/models/backbone.py` | Swin Transformer feature extractor |
| `DepthCNN` | `src/nutrisnap/models/depth_cnn.py` | Lightweight depth feature extractor |
| `ChannelAttentionFusion` | `src/nutrisnap/models/fusion.py` | RGB+depth+scalar fusion |
| `UncertaintyWeightedLoss` | `src/nutrisnap/models/loss.py` | Kendall et al. multi-task loss |
| `NutritionTrainer` | `src/nutrisnap/training/trainer.py` | 3-phase transfer learning |
| `NutriSnapDataset` | `src/nutrisnap/data/dataset.py` | Nutrition5k data loader |
| Preprocessing | `src/nutrisnap/data/preprocessing.py` | RGB/depth/mass correction |
| Rule Validator | `src/nutrisnap/verification/rule_validator.py` | Post-prediction sanity checks |

---

## 🎯 Performance Targets

| Metric | Target |
|---|---|
| Calorie MAE | ≤ 40 kcal |
| Calorie MAPE | ≤ 12% |
| R² | ≥ 0.85 |
| Spearman ρ | ≥ 0.80 |
| Latency (end-to-end) | ≤ 2 s on GTX 1650 |
| VRAM budget | ≤ 4 GB |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- CUDA 11.8+ (GTX 1650 or better)
- 4 GB VRAM minimum

### Installation

```powershell
# Clone the repo
git clone https://github.com/Omprakash-p06/NutriSnap.git
cd NutriSnap

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install package + dev dependencies
pip install -e .
pip install -r requirements-dev.txt
```

### Data Setup

The project uses the [Nutrition5k dataset](https://github.com/google-research-datasets/Nutrition5k) from Kaggle.

```powershell
# Download and configure the dataset
.venv\Scripts\python.exe scripts/setup_dataset.py

# Run ingestion + split generation
make data
```

### Training

**Default (EfficientNetV2-B0 — fastest):**
```powershell
.venv\Scripts\python.exe src/train.py --config configs/experiment/ensemble_5fold.yaml
```

**Highest accuracy (Swin Transformer Tiny):**
```powershell
.venv\Scripts\python.exe src/train.py --config configs/experiment/ensemble_5fold_swin.yaml
```

**Smoke test (dry run, ~30 seconds):**
```powershell
.venv\Scripts\python.exe src/train.py --config configs/experiment/ensemble_5fold.yaml --limit 20 --epochs 1
```

### API Server

```powershell
.venv\Scripts\uvicorn nutrisnap.api.main:app --host 0.0.0.0 --port 8000
```

**Endpoints:**
- `POST /predict` — Upload image, returns `image_id`
- `GET /result/{image_id}` — Retrieve nutrition estimate

---

## 📊 Training Details

### 3-Phase Transfer Learning

| Phase | Epochs | Strategy |
|---|---|---|
| 1 | 0 → 10 | Backbone frozen, train heads + depth branch |
| 2 | 10 → 20 | Last 3 backbone layers/stages unfrozen |
| 3 | 20 → 100 | Full backbone fine-tuning |

### LR Schedule
- 5-epoch linear warmup → Cosine Annealing to `1e-7`
- Gradient clipping at `max_norm=1.0`
- Mixed precision (AMP) + gradient accumulation (effective batch=32)

### Data Strategy
- **80/15/5 dish-level split** (train/test/val) — no cross-dish leakage
- **5-fold stratified CV** on training dishes (stratified by calorie bins)
- **Ingredient-mass correction** during preprocessing (re-scales ingredient masses to match measured dish weight — reduces calorie MAE substantially)
- **Augmentations**: HorizontalFlip, Rotate(±30°), RandomResizedCrop, BrightnessContrast, GaussianBlur, CoarseDropout

### Evaluation Metrics
All metrics are computed per-nutrient `[calories, fat, carbs, protein]`:
- **MAE** — Mean Absolute Error in real units (kcal/g)
- **MAPE** — Epsilon-safe (mask targets < 5g/kcal to avoid near-zero artifacts)
- **R²** — Variance explained by the model
- **Spearman ρ** — Ranking/ordering correlation

---

## 🔬 Verification Pipeline

Every prediction passes through 4 layers before being returned:

1. **Rule-Based Validator** — Hard bounds (50–1500 kcal) + macro-calorie consistency (< 20% error)
2. **LLM Sanity Check** (Gemini Flash) — Triggered on rule violation or high ensemble variance
3. **USDA Cross-Reference** — Compares estimates against FoodData Central
4. **Human Flag** — Escalation for extreme outliers

---

## 📁 Project Structure

```
NutriSnap/
├── configs/
│   ├── data/               # Data pipeline config
│   ├── experiment/         # Training experiments
│   │   ├── ensemble_5fold.yaml       # EfficientNet run
│   │   └── ensemble_5fold_swin.yaml  # Swin Transformer run
│   └── models/
│       ├── efficientnet_v2_b0.yaml
│       └── swin_tiny.yaml
├── src/nutrisnap/
│   ├── api/                # FastAPI endpoints
│   ├── data/               # Dataset, preprocessing, splits
│   ├── models/             # Backbone, DepthCNN, fusion, heads, loss
│   ├── training/           # Trainer (3-phase, metrics)
│   ├── inference/          # Inference pipeline
│   ├── pipeline/           # End-to-end pipeline orchestration
│   └── verification/       # Rule validator + LLM fallback
├── scripts/                # Data prep, audit, smoke checks
├── tests/                  # Test suite
├── misc/
│   ├── ARCHITECTURE.md
│   └── strategy_final_2026-04-16.md  # ← Definitive implementation guide
└── .planning/              # GSD workflow planning artifacts
```

---

## 🧪 Development

```powershell
# Run tests
make test

# Lint check
make lint

# Auto-format
make format

# Smoke-check the pipeline
make smoke-check
```

---

## 📖 Architecture Documentation

For the full architectural rationale, implementation decisions, and gap status:

- [`misc/strategy_final_2026-04-16.md`](misc/strategy_final_2026-04-16.md) — Implementation strategy (v1.1)
- [`misc/ARCHITECTURE.md`](misc/ARCHITECTURE.md) — Full system architecture
- [`misc/revised_implementationplan.md`](misc/revised_implementationplan.md) — Revised plan (rebuild)
- [`.planning/STATE.md`](.planning/STATE.md) — Current project state

---

## 📄 License

MIT — see [LICENSE](LICENSE).
