# Technology Stack

**Analysis Date:** 2026-04-18

**Mapping basis:** This reflects the current dependencies and runtime environment for the NutriSnap modular backend.

## Languages

**Primary:**
- Python 3.10+ - Backend API, ML models, and utility scripts (`src/nutrisnap/`, `scripts/`, `src/train.py`).

**Secondary:**
- YAML and JSON - Hierarchical system configuration (`configs/`) and data storage.
- Markdown - Extensive project documentation (`README.md`, `docs/`, `.planning/`).
- SQL - Persistence logic using SQLite (`src/nutrisnap/api/store.py`).

## Runtime

**Environment:**
- Python application server via `uvicorn` for the FastAPI service.
- Local ML inference supporting both CPU and CUDA (when available).
- Asynchronous background task execution within the FastAPI process for job processing.

**Package Manager:**
- `pip` - Python dependency management via `requirements.txt` and `requirements-dev.txt`.
- `pyproject.toml` - Standard Python project metadata.

## Frameworks

**Core:**
- **FastAPI 0.110+** - Asynchronous web framework for the main API endpoints.
- **aiosqlite** - Async SQLite client for result persistence.
- **Pydantic 2.x** - Data validation and settings management.

**ML / CV:**
- **PyTorch 2.2+** - Core deep learning framework.
- **PyTorch Lightning 2.0+** - Trainer and model lifecycle management.
- **timm** - Pre-trained model backbones (EfficientNet, Swin, etc.).
- **Ultralytics YOLO 8.x** - Used in detection pipeline stages.
- **Segment Anything (SAM) / FoodSAM** - Food-specific image segmentation.
- **Transformers (Hugging Face)** - Pipeline for depth estimation and LLM integrations.
- **Google Generative AI (Gemini)** - LLM-based prediction fallback.
- **Albumentations** - Image augmentation pipeline.
- **OpenCV / NumPy / Pillow** - Standard computer vision utilities.

**Build / Dev:**
- **pytest** - Unit and integration testing.
- **GitHub Actions** - CI/CD for linting and automated testing.
- **Makefile** - Task automation.
- **black / isort / mypy / pylint** - Python code quality and formatting.

## Key Dependencies

**Critical:**
- `torch`, `torchvision`, `pytorch-lightning` - Deep learning stack.
- `fastapi`, `uvicorn`, `aiosqlite` - Web and database layer.
- `segment-anything` - Advanced image segmentation.
- `google-generativeai` - LLM fallback capability.
- `timm` - Model backbones.
- `albumentations` - Training-time augmentations.
- `kagglehub` - Dataset acquisition.

**Infrastructure:**
- `python-multipart` - Form-data file upload support.
- `pyyaml` - Hierarchical configuration parsing.
- `httpx` / `requests` - External API communication (USDA, Gemini).

## Configuration

**System Config:**
- `configs/main.yaml` - Main entry point for system-wide settings.
- `configs/api/`, `configs/data/`, `configs/model/`, `configs/pipeline/` - Sub-configs.

**Environment:**
- `.env` - Local environment variables (API keys, paths).
- Path-based settings for dataset and checkpoint locations.

## Platform Requirements

**Development:**
- Windows/Linux/macOS supported.
- Python 3.10+ required.
- CUDA-compatible GPU recommended for training and high-performance inference.
- FoodSAM weights must be downloaded to `third_party/FoodSAM/checkpoints/`.

**Production:**
- Designed for containerized deployment (Dockerfile-ready, though not currently used).
- Local storage required for SQLite database and temporary upload cache.

---
*Stack analysis: 2026-04-18*
