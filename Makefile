.PHONY: install audit data train test lint format clean help
help:
	@echo "NutriSnap make targets:"
	@echo "  install   Install package and dev dependencies"
	@echo "  audit     Audit Nutrition5k raw dataset"
	@echo "  data      Run audit + ingestion + split generation"
	@echo "  train     Train the nutrition regressor"
	@echo "  test      Run test suite"
	@echo "  lint      Run linters (black, isort, flake8)"
	@echo "  format    Auto-format code (black + isort)"
	@echo "  clean     Remove Python cache files"

install:
	pip install -e .
	pip install -r requirements-dev.txt
	pre-commit install

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
	python scripts/smoke_check_pipeline.py --rgbd-dir data/processed/rgbd

train:
	python src/train.py --config configs/experiment/baseline.yaml

test:
	pytest tests/ -v

lint:
	black src/ tests/ scripts/ --check
	isort src/ tests/ scripts/ --check-only
	flake8 src/ tests/ scripts/ --max-line-length=88 --extend-ignore=E203,W503

format:
	black src/ tests/ scripts/
	isort src/ tests/ scripts/

clean:
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "__pycache__" -delete 2>/dev/null || true
