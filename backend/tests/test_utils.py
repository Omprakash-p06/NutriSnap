"""Tests for NutriSnap utility modules."""

import pytest
from nutrisnap.utils.config_loader import DataConfig, load_config, load_data_config
from nutrisnap.utils.exceptions import ConfigError, DataAuditError, NutriSnapError


def test_data_config_defaults():
    """DataConfig has correct defaults."""
    cfg = DataConfig()
    assert cfg.n_cv_folds == 5
    assert cfg.val_fraction == 0.15
    assert cfg.random_seed == 42


def test_load_config_missing_file():
    """load_config raises ConfigError for missing file."""
    with pytest.raises(ConfigError, match="not found"):
        load_config("/nonexistent/path/config.yaml")


def test_load_data_config_missing_file():
    """load_data_config raises ConfigError for missing file."""
    with pytest.raises(ConfigError, match="not found"):
        load_data_config("/nonexistent/path/data_config.yaml")


def test_nutrisnap_error_hierarchy():
    """NutriSnapError is base for all custom exceptions."""
    assert issubclass(ConfigError, NutriSnapError)
    assert issubclass(DataAuditError, NutriSnapError)


def test_data_config_calorie_bins_default():
    """DataConfig calorie_bins has expected default values."""
    cfg = DataConfig()
    assert cfg.calorie_bins == [0, 200, 400, 600, 800, 1000, 2000]


def test_data_config_from_yaml(tmp_path):
    """load_data_config reads and validates YAML file correctly."""
    cfg_file = tmp_path / "data_config.yaml"
    cfg_file.write_text("n_cv_folds: 3\nrandom_seed: 99\n")
    cfg = load_data_config(cfg_file)
    assert cfg.n_cv_folds == 3
    assert cfg.random_seed == 99
