"""Tests for the NutritionValidator rule engine."""
import pytest
from nutrisnap.pipeline.validator import NutritionValidator


class TestNutritionValidator:
    """Verify that the validator correctly identifies plausible/implausible nutrition."""

    @pytest.fixture
    def validator(self):
        return NutritionValidator()

    def test_valid_prediction(self, validator):
        """Correct Atwater and density should pass."""
        preds = {"calories": 100, "fat": 5, "carbs": 10, "protein": 3.75}
        # 4*3.75 + 4*10 + 9*5 = 15 + 40 + 45 = 100
        is_p, reason = validator.validate(preds, volume_cm3=50, area_cm2=10)
        assert is_p
        assert reason is None

    def test_atwater_failure(self, validator):
        """Inconsistent macros should be flagged."""
        preds = {"calories": 500, "fat": 0, "carbs": 0, "protein": 0}
        is_p, reason = validator.validate(preds, volume_cm3=50, area_cm2=10)
        assert not is_p
        assert "Atwater inconsistency" in reason

    def test_density_too_high(self, validator):
        """1000 calories in 1cm3 is physically impossible (max is ~9)."""
        preds = {"calories": 1000, "fat": 100, "carbs": 25, "protein": 0} # 900+100=1000
        is_p, reason = validator.validate(preds, volume_cm3=1, area_cm2=1)
        assert not is_p
        assert "Energy density too high" in reason

    def test_geometric_anomaly(self, validator):
        """A 1000cm3 object with 1cm2 area is too tall/pipe-like."""
        preds = {"calories": 100, "fat": 5, "carbs": 10, "protein": 3.75}
        is_p, reason = validator.validate(preds, volume_cm3=1000, area_cm2=1)
        assert not is_p
        assert "Geometric anomaly: Object too tall" in reason
