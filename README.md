# NutriSnap

NutriSnap is a lightweight, production-oriented AI system that estimates calories, protein, carbohydrates, and fats from a single meal photo.

## Architecture

NutriSnap implements a modular research-backed pipeline:
1. **Segmentation**: Isolates individual food items using FoodSAM.
2. **Volume Estimation**: Estimates 3D volume using FoodVolume (MVP depth backbone).
3. **Nutrition Regression**: Regresses macro-nutrients using an EfficientNetV2-B0 multi-task head trained on Nutrition5k.
4. **Validation**: Rule-based verification with optional LLM fallback for high-uncertainty outputs.

## Setup

### Prerequisites
- Python 3.10+
- CUDA-capable GPU (GTX 1650 4GB recommended minimum)
- Git

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd NutriSnap

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in editable mode with dependencies
pip install -e .
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 2. External Model Setup (FoodSAM)
NutriSnap uses FoodSAM for segmentation. Fetch the pre-trained weights (~2.4 GB):

```bash
python scripts/setup_foodsam.py
```

## API Usage

NutriSnap provides a production-style FastAPI backend with an asynchronous Job/Polling pattern.

### Starting the Server
```bash
# Start the API server
uvicorn nutrisnap.api.main:app --host 0.0.0.0 --port 8000
```

### Submit a Prediction
```bash
curl -X POST -F "file=@meal.jpg" http://localhost:8000/predict
# Returns: {"job_id": "uuid", "status": "pending", ...}
```

### Poll for Results
```bash
curl http://localhost:8000/result/<job_id>
# Returns: {"job_id": "...", "status": "completed", "result": {"calories": 450, ...}}
```

### Mock Mode (for testing)
Set `NUTRISNAP_MOCK_CV=true` to skip heavy ML steps and verify infrastructure.

## Data Setup & Training

NutriSnap uses the [Nutrition5k dataset](https://www.kaggle.com/datasets/gillesokhin/nutrition5k-dataset).

### 1. Dataset Acquisition
Download the dataset from Kaggle and place it at:
`data/raw/archive (4)/`

### 2. Run the Data Pipeline
Execute the automated pipeline to audit, ingest, and prepare features:

```bash
# Audit raw dataset + ingest + generate splits
make data

# Generate RGB-D artifacts (Segmentations + Depth Maps)
make preprocess

# Extract volume-based features
make volume-features
```

### 3. Training & Validation
Train the nutrition regressor and verify performance:

```bash
# Start training (configured for 4GB VRAM)
make train

# Run test suite
make test

# (Optional) Full pipeline smoke check
make smoke-check
```

After `make data`, the following artifacts will be available:
- `data/splits/train_ids.txt` — training dish IDs
- `data/splits/val_ids.txt` — validation dish IDs (15% of train)
- `data/splits/test_ids.txt` — held-out test dish IDs
- `data/splits/cv_folds.json` — 5-fold CV fold assignments
- `data/splits/mvp_subset_ids.txt` — 8-dish MVP subset
- `configs/data/selected_dishes.json` — MVP dish details
- `reports/audit_report.json` — dataset audit results

## Development

```bash
make install      # Install package + dev deps + pre-commit hooks
make audit        # Audit raw Nutrition5k data
make data         # Full data pipeline (audit -> ingest -> splits)
make train        # Train the nutrition regressor
make test         # Run test suite
make lint         # Check code quality (black, isort, flake8)
make format       # Auto-format code (black + isort)
make clean        # Remove Python cache files
```

## Project Structure

```
NutriSnap/
├── configs/                  # Config hub (YAML + JSON)
│   ├── data/                 # Data paths, split params, MVP subset
│   ├── model/                # Model architecture hyperparams
│   └── experiment/           # Composable experiment configs
├── data/
│   ├── raw/                  # Original Nutrition5k (immutable)
│   ├── interim/              # Normalized intermediate CSVs
│   ├── processed/            # Segmented + preprocessed data
│   └── splits/               # Train/val/test/CV split files
├── docs/                     # API reference, data dictionary, model card
├── src/nutrisnap/
│   ├── data/                 # Dataset, DataModule, preprocessing, splits
│   ├── models/               # Backbone, heads, loss, Lightning module
│   ├── pipeline/             # FoodSAM segmenter + FoodVolume estimator
│   ├── utils/                # Metrics, config loader, logger, device
│   └── verification/         # Rule validator + LLM fallback
├── scripts/                  # Data pipeline scripts
├── tests/                    # Unit + integration tests
├── reports/                  # Audit report, evaluation metrics
└── results/                  # Predictions, training logs
```

For more details on the architecture, see [misc/ARCHITECTURE.md](misc/ARCHITECTURE.md).

## Hardware Requirements

- **Minimum**: GTX 1650 with 4GB VRAM
- **Training**: Uses mixed precision (FP16) + gradient accumulation to stay within 4GB
- **Inference**: Target ≤2 seconds per image on the minimum hardware