.PHONY: install audit data train test lint format clean help
help:
	@echo "NutriSnap make targets:"
	@echo "  install   Install package and dev dependencies"
	@echo "  setup-data Download selective MVP dataset from Kaggle"
	@echo "  audit     Audit Nutrition5k raw dataset"
	@echo "  data      Run audit + ingestion + split generation"
	@echo "  train     Train the nutrition regressor"
	@echo "  test      Run test suite"
	@echo "  lint      Run linters (black, isort, flake8)"
	@echo "  format    Auto-format code (black + isort)"
	@echo "  clean     Remove Python cache files"

install:
	pip install -e .
	pip install -r requirements.txt
	pre-commit install

setup-data:
	python scripts/setup_dataset.py

audit:
	python scripts/audit_dataset.py --config configs/data/data_config.yaml

data: audit
	python scripts/ingest_nutrition5k.py --config configs/data/data_config.yaml
	python scripts/generate_splits.py --config configs/data/data_config.yaml

preprocess:
	python scripts/generate_rgbd_artifacts.py --config configs/data/data_config.yaml

volume-features:
	python scripts/generate_volume_features.py --config configs/data/data_config.yaml

smoke-check:
	python scripts/smoke_check_pipeline.py --rgbd-dir datasets/processed/rgbd

train:
	python nutrisnap/train.py --config configs/experiment/baseline.yaml

test:
	pytest tests/ -v

lint:
	black app/ nutrisnap/ tests/ scripts/ --check
	isort app/ nutrisnap/ tests/ scripts/ --check-only
	flake8 app/ nutrisnap/ tests/ scripts/

format:
	black app/ nutrisnap/ tests/ scripts/
	isort app/ nutrisnap/ tests/ scripts/

clean:
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "__pycache__" -delete 2>/dev/null || true
