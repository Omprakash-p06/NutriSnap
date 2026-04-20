# Codebase Structure

**Analysis Date:** 2026-04-18

**Mapping basis:** The tree below reflects the current project layout centered around the `src/nutrisnap/` package structure.

## Directory Layout

```text
NutriSnap/
├── .github/            # GitHub Actions workflows for CI/CD
├── configs/            # Hierarchical YAML/JSON configuration files
│   ├── api/            # API and background worker settings
│   ├── data/           # Dataset and preprocessing parameters
│   ├── experiment/     # Training and evaluation experiment configs
│   ├── model/          # Model architecture definitions
│   └── pipeline/       # Inference pipeline component settings
├── data/               # Project data storage
│   ├── raw/            # Original datasets (e.g., Nutrition5k)
│   ├── processed/      # Cleaned and formatted data for training
│   ├── splits/         # Training/validation/test split definitions
│   └── uploads/        # Temporary storage for API image uploads
├── docs/               # Technical documentation and guides
├── misc/               # Architectural diagrams and legacy redesign notes
├── models/             # Local storage for model checkpoints and weights
├── notebooks/          # Research and EDA notebooks
├── reports/            # Generated evaluation and audit results
├── scratch/            # Temporary experimental scripts and verification tools
├── scripts/            # Standalone maintenance and data processing scripts
├── src/                # Python source code
│   ├── train.py        # Root-level training entry point
│   └── nutrisnap/      # Main application package
│       ├── api/        # FastAPI, job storage, and worker logic
│       ├── data/       # Dataset classes, augmentation, and preprocessing
│       ├── inference/  # High-level inference and ensemble orchestration
│       ├── models/     # Neural network architecture definitions
│       ├── pipeline/   # Modular inference pipeline components
│       ├── training/   # Trainer classes and training loop logic
│       ├── utils/      # Shared utilities (logging, metrics, config)
│       └── verification/ # Post-prediction validation (USDA, rules)
├── tests/              # Comprehensive test suite (unit, integration, pipeline)
├── third_party/        # External submodules (e.g., FoodSAM)
├── .gitignore          # Git ignore patterns
├── Makefile            # Automation commands for setup and execution
├── pyproject.toml      # Project metadata and tool configuration
├── README.md           # Project overview and setup instructions
├── requirements.txt    # Production dependencies
└── requirements-dev.txt # Development and testing dependencies
```

## Directory Purposes

**`src/nutrisnap/api/`:**
- Purpose: Web API surface and asynchronous job processing.
- Key files: `main.py` (FastAPI), `worker.py` (Orchestrator), `store.py` (SQLite persistence).

**`src/nutrisnap/pipeline/`:**
- Purpose: Orchestrates the multi-stage inference process.
- Key files: `inference.py` (Pipeline runner), `segmenter.py`, `volume.py`, `fallback.py`.

**`src/nutrisnap/models/`:**
- Purpose: Core model architectures and building blocks.
- Key files: `backbone.py`, `nutrition_regressor.py`, `fusion.py`, `loss.py`.

**`src/nutrisnap/data/`:**
- Purpose: Data loading, cleaning, and transformation.
- Key files: `dataset.py`, `preprocessing.py`, `augmentation.py`.

**`configs/`:**
- Purpose: Centralized configuration management using nested YAML files.
- Patterns: `main.yaml` aggregates sub-configs for specific runs.

**`scripts/`:**
- Purpose: Developer tools for data ingestion and environment setup.
- Key files: `prepare_data.py`, `ingest_nutrition5k.py`, `setup_foodsam.py`.

**`tests/`:**
- Purpose: Automated verification of all system layers.
- Subdirectories: Mirroring `src/nutrisnap/` structure for unit tests.

## Key File Locations

**Entry Points:**
- `src/nutrisnap/api/main.py` - FastAPI app.
- `src/train.py` - Model training.
- `scripts/preprocess_full.py` - End-to-end data preparation.

**Configuration:**
- `configs/main.yaml` - Primary config entry.
- `requirements.txt` - Dependency list.

**Data Assets:**
- `data/nutrisnap.db` - Job and result tracking database.
- `models/checkpoints/` - Saved model states.

## Naming Conventions

**Files:**
- Python: `snake_case.py`.
- Configs: `snake_case.yaml`.
- Documentation: `UPPER_CASE.md` or `snake_case.md`.

**Classes & Functions:**
- Classes: `PascalCase`.
- Functions/Methods: `snake_case`.

## Where to Add New Code

**New Pipeline Stage:**
- Implementation: `src/nutrisnap/pipeline/`
- Configuration: `configs/pipeline/`

**New Model Type:**
- Definition: `src/nutrisnap/models/`
- Config: `configs/model/`

**New Data Source:**
- Ingestion script: `scripts/`
- Dataset class: `src/nutrisnap/data/dataset.py`

---
*Structure analysis: 2026-04-18*
