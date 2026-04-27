# Directory Structure

**Refresh Date:** 2026-04-27

## Root Directory
- `NutriSnap/`: Core backend and ML repository.
- `frontend/`: React PWA repository.
- `.planning/`: GSD workflow artifacts and codebase documentation.
- `.github/`: CI/CD workflows.

## NutriSnap (Backend) Breakdown
- `src/nutrisnap/`: Main package.
  - `api/`: FastAPI routes (`main.py`), models, and background workers.
  - `data/`: Datasets, preprocessing logic, and data splitting.
  - `inference/`: Ensemble and high-level inference logic.
  - `models/`: Neural network architectures (ViT, EfficientNet, Fusion).
  - `pipeline/`: Core pipeline stages (Segmentation, Depth, Volume, Multi-Food).
  - `training/`: Model training scripts and trainers.
  - `utils/`: Configuration loaders, logging, and metrics.
  - `verification/`: LLM-based validation and USDA service integration.
- `scripts/`: Data ingestion and preparation scripts.
- `configs/`: YAML configurations for models and pipelines.
- `tests/`: Unit and integration tests.

## Frontend (PWA) Breakdown
- `src/`: Main source.
  - `components/`: UI components organized by domain.
    - `animations/`: Motion-based components.
    - `common/`: Reusable UI primitives (Buttons, Cards, Modals).
    - `dashboard/`: Widgets and lists for the dashboard view.
    - `layout/`: Hero sections, Navbars, and Page layouts.
    - `scanning/`: Camera interface and results visualization.
    - `social/`: Community feed components.
  - `context/`: Auth and Theme context providers.
  - `hooks/`: Custom React hooks (e.g., `useMealHistory`).
  - `pages/`: Top-level page components (Home).
  - `services/`: API client and external service wrappers.
- `public/`: Static assets and PWA manifest.
- `elements/`: Raw HTML/CSS elements (if any).

## Data & Artifacts
- `data/`: Raw and processed dataset files.
- `models/checkpoints/`: Trained model weights.
- `reports/`: Generated analysis and performance reports.
