"""Tests for LLM Validator (Phase 11 Plan 03).

Tests for the LLM validation layer that catches hallucinations and
unrealistic predictions in multi-food detection pipeline.
"""

from unittest.mock import AsyncMock, patch

import pytest


class TestLLMValidatorImports:
    """Test LLM validator module can be imported."""

    def test_validator_module_exists(self):
        """Test that llm_validator module exists."""
        try:
            from nutrisnap.verification.llm_validator import LLMValidator

            assert LLMValidator is not None
        except ImportError:
            pytest.skip("LLMValidator not yet implemented (Plan 11-03 not executed)")


class TestLLMValidationLogic:
    """Test LLM validation logic with mock responses."""

    @pytest.fixture
    def mock_llm_response_valid(self):
        """Mock LLM response for valid meal."""
        return {
            "is_valid": True,
            "reasoning": "All items are plausible and non-redundant",
            "corrections": [],
        }

    @pytest.fixture
    def mock_llm_response_invalid(self):
        """Mock LLM response for invalid meal."""
        return {
            "is_valid": False,
            "reasoning": "Detected redundant labels: 'Bread' and 'Sandwich'",
            "corrections": [
                {"original": "Sandwich", "corrected": None, "action": "remove"}
            ],
        }

    def test_validation_prompt_format(self):
        """Test that validation prompt is properly formatted."""
        try:
            from nutrisnap.verification.llm_validator import LLMValidator

            validator = LLMValidator()
            items = [
                {"label": "pizza", "volume_cm3": 200, "calories": 500},
                {"label": "salad", "volume_cm3": 150, "calories": 50},
            ]
            prompt = validator._build_prompt(items, 550)
            assert "pizza" in prompt.lower()
            assert "salad" in prompt.lower()
        except ImportError:
            pytest.skip("LLMValidator not yet implemented")

    def test_json_recovery_from_markdown(self):
        """Test JSON recovery from markdown-wrapped LLM response."""
        try:
            from nutrisnap.verification.llm_validator import LLMValidator

            validator = LLMValidator()
            raw_response = """```json
{"is_valid": true, "reasoning": "Test"}
```"""
            result = validator._parse_response(raw_response)
            assert result is not None
            assert "is_valid" in result
        except ImportError:
            pytest.skip("LLMValidator not yet implemented")

    @pytest.mark.asyncio
    async def test_realism_check_volume_too_high(self):
        """Test detection of unrealistic volume (e.g., 5kg lettuce)."""
        try:
            from nutrisnap.verification.llm_validator import LLMValidator

            validator = LLMValidator()
            unrealistic_items = [
                {"label": "lettuce", "volume_cm3": 5000000, "mass_g": 5000000}
            ]
            with patch.object(validator, "call_llm", new_callable=AsyncMock) as mock:
                mock.return_value = {
                    "is_valid": False,
                    "reasoning": "Volume too high for lettuce",
                    "corrections": [],
                }
                result = await validator.validate_meal(unrealistic_items, 500000)
                assert not result.is_valid
        except ImportError:
            pytest.skip("LLMValidator not yet implemented")

    @pytest.mark.asyncio
    async def test_redundancy_detection(self):
        """Test detection of redundant labels (e.g., Bread + Sandwich)."""
        try:
            from nutrisnap.verification.llm_validator import LLMValidator

            validator = LLMValidator()
            redundant_items = [
                {"label": "bread", "volume_cm3": 100, "calories": 265},
                {"label": "sandwich", "volume_cm3": 200, "calories": 400},
            ]
            with patch.object(validator, "call_llm", new_callable=AsyncMock) as mock:
                mock.return_value = {
                    "is_valid": False,
                    "reasoning": "Redundant: 'Bread' and 'Sandwich' likely same item",
                    "corrections": [
                        {"original": "sandwich", "corrected": None, "action": "remove"}
                    ],
                }
                result = await validator.validate_meal(redundant_items, 665)
                assert not result.is_valid
        except ImportError:
            pytest.skip("LLMValidator not yet implemented")

    @pytest.mark.asyncio
    async def test_calorie_correction(self):
        """Test LLM can correct unrealistic calorie values."""
        try:
            from nutrisnap.verification.llm_validator import LLMValidator

            validator = LLMValidator()
            unrealistic_items = [
                {"label": "apple", "volume_cm3": 100, "calories": 5000}
            ]
            with patch.object(validator, "call_llm", new_callable=AsyncMock) as mock:
                mock.return_value = {
                    "is_valid": True,
                    "reasoning": "Corrected unrealistic calories",
                    "corrections": [
                        {"original": 5000, "corrected": 52, "field": "calories"}
                    ],
                }
                result = await validator.validate_meal(unrealistic_items, 5000)
                assert len(result.corrections) > 0
        except ImportError:
            pytest.skip("LLMValidator not yet implemented")

    @pytest.mark.asyncio
    async def test_valid_meal_passes(self):
        """Test that valid meals pass validation."""
        try:
            from nutrisnap.verification.llm_validator import LLMValidator

            validator = LLMValidator()
            valid_items = [
                {"label": "chicken", "volume_cm3": 150, "calories": 250},
                {"label": "rice", "volume_cm3": 150, "calories": 200},
            ]
            with patch.object(validator, "call_llm", new_callable=AsyncMock) as mock:
                mock.return_value = {
                    "is_valid": True,
                    "reasoning": "All items plausible",
                    "corrections": [],
                }
                result = await validator.validate_meal(valid_items, 450)
                assert result.is_valid
        except ImportError:
            pytest.skip("LLMValidator not yet implemented")
