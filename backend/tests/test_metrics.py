"""Tests for diagnostic metrics and failure detection."""

import pytest

from nutrisnap.utils.metrics import (
    binned_mae,
    calorie_mae,
    calorie_mape,
    prediction_variance_ratio,
    spearman_correlation,
)


class TestMetrics:
    """Verify that metrics correctly calculate regression quality and detect failure modes."""

    def test_calorie_mae(self):
        y_true = [100, 200, 300]
        y_pred = [110, 190, 310]
        # |10-10+10|/3 = 10
        assert calorie_mae(y_true, y_pred) == pytest.approx(10.0)

    def test_calorie_mape(self):
        y_true = [100, 200]
        y_pred = [130, 140]
        # |(30/100) + (60/200)| / 2 = (0.3 + 0.3) / 2 = 0.3 -> 30%
        assert calorie_mape(y_true, y_pred) == pytest.approx(30.0)

    def test_mape_zeros(self):
        # Should ignore zero targets
        y_true = [0, 100]
        y_pred = [50, 110]
        # |10/100| = 0.1 -> 10%
        assert calorie_mape(y_true, y_pred) == pytest.approx(10.0)

    def test_spearman_correlation(self):
        # Perfectly monotonic
        y_true = [1, 2, 3, 4, 5]
        y_pred = [10, 20, 30, 40, 50]
        assert spearman_correlation(y_true, y_pred) == pytest.approx(1.0)

        # Inverted
        y_pred = [50, 40, 30, 20, 10]
        assert spearman_correlation(y_true, y_pred) == pytest.approx(-1.0)

    def test_variance_ratio_detects_collapse(self):
        y_true = [100, 200, 300, 400]
        # Constant prediction (mean collapse)
        y_pred = [250, 250, 250, 250]
        ratio = prediction_variance_ratio(y_true, y_pred)
        assert ratio == 0.0

        # Normal variation
        y_pred = [110, 210, 310, 410]
        ratio = prediction_variance_ratio(y_true, y_pred)
        assert ratio == pytest.approx(1.0)

    def test_binned_mae(self):
        y_true = [50, 150, 500, 1200]
        y_pred = [60, 160, 550, 1300]
        bins = [0, 200, 800, 2000]

        results = binned_mae(y_true, y_pred, bins)

        # 0-200 bin: |50-60| and |150-160| -> MAE 10
        assert results["0-200 kcal"] == pytest.approx(10.0)
        # 200-800 bin: |500-550| -> MAE 50
        assert results["200-800 kcal"] == pytest.approx(50.0)
        # 800-2000 bin: |1200-1300| -> MAE 100
        assert results["800-2000 kcal"] == pytest.approx(100.0)
