"""Config loader using PyYAML + Pydantic for type-safe config management."""
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from nutrisnap.utils.exceptions import ConfigError


class DataConfig(BaseModel):
    """Configuration for data paths and split parameters."""

    raw_dir: str = "data/raw"
    interim_dir: str = "data/interim"
    processed_dir: str = "data/processed"
    splits_dir: str = "data/splits"
    external_dir: str = "data/external"
    mvp_dish_count: int = Field(default=8, ge=1, le=50)
    val_fraction: float = Field(default=0.15, gt=0.0, lt=1.0)
    test_fraction: float = Field(default=0.15, gt=0.0, lt=1.0)
    n_cv_folds: int = Field(default=5, ge=2, le=10)
    random_seed: int = 42
    calorie_bins: list[int] = [0, 200, 400, 600, 800, 1000, 2000]


class NutriSnapConfig(BaseModel):
    """Root configuration for NutriSnap."""

    data: DataConfig = Field(default_factory=DataConfig)
    project_root: str = "."


def load_config(path: str | Path) -> NutriSnapConfig:
    """Load and validate a YAML config file.

    Args:
        path: Path to YAML config file.

    Returns:
        Validated NutriSnapConfig.

    Raises:
        ConfigError: If file not found or validation fails.
    """
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    try:
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
        return NutriSnapConfig(**raw)
    except Exception as e:
        raise ConfigError(f"Failed to load config from {path}: {e}") from e


def load_data_config(path: str | Path) -> DataConfig:
    """Load and validate a data-specific YAML config file.

    Args:
        path: Path to data YAML config file.

    Returns:
        Validated DataConfig.

    Raises:
        ConfigError: If file not found or validation fails.
    """
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Data config file not found: {path}")
    try:
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
        return DataConfig(**raw)
    except Exception as e:
        raise ConfigError(f"Failed to load data config from {path}: {e}") from e
