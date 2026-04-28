"""Tests for SequentialOrchestrator (mock backend)."""

import pytest

from app.services.orchestrator import PipelineResult, SequentialOrchestrator


@pytest.fixture
def mock_orchestrator():
    return SequentialOrchestrator(mock=True)


def test_mock_predict_returns_result(mock_orchestrator, tmp_path):
    # Create a dummy image path — mock doesn't actually open it
    fake_img = str(tmp_path / "meal.jpg")
    result = mock_orchestrator.predict(fake_img)
    assert isinstance(result, PipelineResult)
    assert result.item_count >= 1
    assert result.total_calories > 0
    assert result.latency_seconds >= 0


def test_mock_predict_has_valid_items(mock_orchestrator, tmp_path):
    fake_img = str(tmp_path / "meal.jpg")
    result = mock_orchestrator.predict(fake_img)
    for item in result.items:
        assert "label" in item
        assert "mass_g" in item
        assert "calories" in item


def test_mock_to_dict(mock_orchestrator, tmp_path):
    fake_img = str(tmp_path / "meal.jpg")
    result = mock_orchestrator.predict(fake_img)
    d = result.to_dict()
    assert isinstance(d, dict)
    assert "items" in d
    assert "total_calories" in d
    assert "validation_summary" in d


def test_teardown_does_not_raise(mock_orchestrator):
    mock_orchestrator.teardown()  # should be a no-op
