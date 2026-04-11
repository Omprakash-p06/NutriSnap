# Phase 1 Research: Foundation & Data Contracts

*Researched: 2026-04-11*
*Phase Requirements: DATA-01, DATA-02, DATA-03, DATA-04, ENG-01*

---

## Nutrition5k Dataset Structure

**Dish ID format:** `dish_[10-digit-unix-timestamp]` (e.g., `dish_1698765432`). Each dish may have multiple scans (incremental photographing of the same plate from different angles). All scans of one dish must remain in the same split to avoid leakage.

**Current raw data layout (confirmed in repo):**
```
data/raw/archive (4)/
├── dish_ingredients.csv       # Per-ingredient breakdown per dish
├── dish_nutrition_values.csv  # dish_id + total macros + per-ingredient detail
├── ingredients_metadata.csv   # Ingredient taxonomy/metadata
└── imagery/
    ├── realsense_overhead/    # Overhead RGB-D images (RealSense camera)
    └── side_angles/           # Side-angle images
```

**dish_nutrition_values.csv columns (confirmed Nutrition5k schema):**
- `dish_id` — unique dish identifier
- `total_calories` — total kcal
- `total_mass` — grams
- `total_fat`, `total_carb`, `total_protein` — macros in grams
- Followed by per-ingredient rows for each scan

**Official train/test splits:** The Nutrition5k GitHub repo provides pre-defined `dish_ids/splits/` containing `train_ids.txt` and `test_ids.txt`. The key constraint is that ALL scans of the same plate go into one partition to prevent data leakage.

**Imagery format:** Overhead RealSense images are RGB-D pairs (color + depth). The depth channel is 16-bit PNG (values in mm). Overhead single-camera view is the primary input per the architecture decision.

---

## Split Strategy

**Key constraint:** Group by `dish_id` — all scans of the same dish must land in the same fold/split. This requires `group=dish_id` in any sklearn splitter.

**Recommended sklearn approach:**

```python
from sklearn.model_selection import StratifiedGroupKFold, GroupShuffleSplit
import numpy as np

# Calorie stratification bins
calorie_bins = [0, 200, 400, 600, 800, 1000, 2000]
df["calorie_bin"] = pd.cut(df["total_calories"], bins=calorie_bins, labels=False)

# For validation split from training set
gss = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=42)
train_idx, val_idx = next(gss.split(X_train, y_train, groups=dish_ids_train))

# For 5-fold CV
sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
folds = list(sgkf.split(X, y_stratified, groups=dish_ids))
```

**Split artifact format (data/splits/):**
- `train_ids.txt` — one dish_id per line (official Nutrition5k train partition)
- `test_ids.txt` — one dish_id per line (official Nutrition5k test partition)
- `val_ids.txt` — subset of train_ids carved out for validation (GroupShuffleSplit)
- `mv_subset_ids.txt` — 5–10 selected dish_ids for MVP training scope
- `cv_folds.json` — see CV Fold Artifact Format section

**Leakage validation:** After split generation, assert `set(train_ids) & set(test_ids) == set()` and `set(train_ids) & set(val_ids) == set()` with informative error messages.

---

## Python Packaging (pyproject.toml)

Use modern `pyproject.toml` with `setuptools` for a `src/` layout:

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "nutrisnap"
version = "0.1.0"
requires-python = ">=3.10"

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 88
target-version = ["py310"]

[tool.isort]
profile = "black"

[tool.mypy]
python_version = "3.10"
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v"
```

The `src/` layout requires `pip install -e .` during setup so `import nutrisnap` resolves correctly. This must be documented in the Makefile and README.

**Two requirements files:**
- `requirements.txt` — runtime: torch, torchvision, timm, albumentations, opencv-python, Pillow, PyYAML, pydantic, numpy, pandas, scikit-learn, fastapi, uvicorn
- `requirements-dev.txt` — dev: pytest, black, isort, flake8, mypy, pre-commit

---

## Config Management Strategy

**Decision: PyYAML + Pydantic (not Hydra for Phase 1)**

Hydra adds significant complexity for an MVP phase. Phase 1 should establish a Pydantic-validated YAML pattern that can optionally be upgraded to Hydra later.

```python
# src/utils/config_loader.py
from pydantic import BaseModel
import yaml
from pathlib import Path

class DataConfig(BaseModel):
    raw_dir: str
    interim_dir: str
    processed_dir: str
    splits_dir: str
    mvp_dish_count: int = 8
    val_fraction: float = 0.15
    n_cv_folds: int = 5
    random_seed: int = 42

def load_config(path: str) -> DataConfig:
    with open(path) as f:
        d = yaml.safe_load(f)
    return DataConfig(**d)
```

**Config file locations:**
- `configs/data/data_config.yaml` — data paths, split params, MVP params
- `configs/data/selected_dishes.json` — MVP dish subset mapping
- `configs/main.yaml` — root config referencing sub-configs

---

## Makefile Patterns

Standard ML-project Makefile targets (POSIX-compatible, Windows-tolerant with `python -m` prefix):

```makefile
.PHONY: install data audit splits train test lint clean

install:
	pip install -e .
	pip install -r requirements-dev.txt
	pre-commit install

audit:
	python scripts/audit_dataset.py

data: audit
	python scripts/ingest_nutrition5k.py
	python scripts/generate_splits.py

train:
	python src/train.py --config configs/experiment/baseline.yaml

test:
	pytest tests/ -v

lint:
	black src/ tests/ scripts/ --check
	isort src/ tests/ scripts/ --check
	flake8 src/ tests/ scripts/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
```

---

## Pre-commit Hook Setup

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ["--max-line-length=88", "--extend-ignore=E203,W503"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        args: ["--ignore-missing-imports"]
```

---

## Dataset Audit Patterns

**Audit script responsibilities (`scripts/audit_dataset.py`):**

1. **Enumerate dish_ids** from `dish_nutrition_values.csv`
2. **Check imagery existence** — for every dish_id verify at least one overhead RGB image exists
3. **Detect corruption** — open each image with PIL (`Image.open(path).verify()`) and catch exceptions
4. **Check annotation completeness** — verify `total_calories`, `total_fat`, `total_carb`, `total_protein` are non-null and positive
5. **Report summary** — print counts: total dishes, dishes with missing imagery, dishes with corrupt images, dishes with incomplete annotations
6. **Write audit_report.json** to `reports/` — structured record for CI/reproducibility

```python
# Pattern for corruption detection
from PIL import Image

def check_image(path):
    try:
        img = Image.open(path)
        img.verify()  # checks for corrupt headers
        return True
    except Exception as e:
        return False
```

**Exit code convention:** `sys.exit(1)` if any critical issues found (missing imagery or null macros). This enables `make audit` to fail clearly in CI.

---

## CV Fold Artifact Format

Store `data/splits/cv_folds.json` as:

```json
{
  "n_folds": 5,
  "created": "2026-04-11",
  "random_seed": 42,
  "stratification": "calorie_bins",
  "grouping": "dish_id",
  "folds": [
    {
      "fold_id": 0,
      "train_ids": ["dish_1698765432", "dish_1698765433", ...],
      "val_ids": ["dish_1698765480", ...]
    },
    {
      "fold_id": 1,
      "train_ids": [...],
      "val_ids": [...]
    }
    ...
  ]
}
```

This format supports:
- Direct indexing by fold_id for training scripts
- Human-readable inspection
- JSON serializable (no numpy types — convert with `.tolist()`)

---

## Validation Architecture

Each plan in Phase 1 should have verifiable test criteria. Here is what to validate:

### Plan 01-01 (Scaffold)
- Directory tree matches spec: `configs/`, `data/{raw,interim,processed,splits,external}`, `src/`, `scripts/`, `tests/`, `reports/`, `results/`, `docs/`, `notebooks/`, `models/` all exist
- `pyproject.toml` exists and `pip install -e .` succeeds
- `from nutrisnap.utils.config_loader import load_config` imports without error
- `.pre-commit-config.yaml` exists; `pre-commit run --all-files` exits 0 on stub files
- `Makefile` exists; `make --dry-run lint` outputs the expected commands

### Plan 01-02 (Audit & Splits)
- `scripts/audit_dataset.py` exits 0 on valid data, 1 on corrupt/missing
- `reports/audit_report.json` is created after audit
- `data/splits/train_ids.txt`, `test_ids.txt` exist and are non-empty
- `set(train_ids) & set(test_ids) == set()` assertion holds
- `data/splits/val_ids.txt` contains 10–20% of train_ids count
- MVP subset: `configs/data/selected_dishes.json` exists with 5–10 dish entries

### Plan 01-03 (CV Artifacts & Docs)
- `data/splits/cv_folds.json` exists with `n_folds=5` key
- Each fold has `train_ids` and `val_ids` keys with non-empty lists
- No dish_id appears in both train_ids and val_ids in the same fold
- `docs/data_dictionary.md` describes column formats for all CSVs
- README.md contains `## Setup` section with install instructions

---

## Key Implementation Decisions

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| Config system | PyYAML + Pydantic (not Hydra) | Simpler for Phase 1; Hydra can be adopted later |
| Raw data path | Keep at `data/raw/archive (4)/` initially, add symlink or path config | Avoid moving actual Nutrition5k files; configure path in data_config.yaml |
| Official splits | Use Nutrition5k splits from GitHub as reference; if not downloaded, derive from CSV | The official splits txt files may not be in the Kaggle download; need fallback |
| Subset strategy | Select by dish variety + calorie range spread | Ensure MVP covers different calorie ranges for good stratification |
| Fold storage | JSON (not pickle) for portability | JSON is reproducible, versionable, and human-readable |
| src layout | `pip install -e .` required | Without editable install, relative imports inside `src/` won't resolve |
| gitignore | Add `data/raw/`, `data/interim/`, `data/processed/`, `models/`, `results/logs/` | Large files should not be committed |

---

## References

- Nutrition5k paper and dataset: https://github.com/google-research-datasets/Nutrition5k
- DietAI24 (Nutrition5k preprocessing reference): https://github.com/Runz96/DietAI24
- Nutrition5k Utilities (OpenSeeD masks): https://github.com/Oatsty/nutrition5k
- FoodSAM (segmentation — Phase 2): https://github.com/jamesjg/FoodSAM
- FoodVolume (volume estimation — Phase 3): https://github.com/leonbegiristain/FoodVolume
- VolETA (volume estimation alternative): https://github.com/GCVCG/VolETA-MetaFood
- scikit-learn StratifiedGroupKFold: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html
- Cookiecutter Data Science structure: https://drivendata.github.io/cookiecutter-data-science/
- pyproject.toml src layout: https://setuptools.pypa.io/en/latest/userguide/package_discovery.html
