"""Tests for NutriSnap pipeline components — segmenter."""

from unittest.mock import patch

import pytest

from nutrisnap.utils.exceptions import InferenceError


class TestFoodSegmenterImport:
    """Tests that FoodSegmenter can be imported."""

    def test_segmenter_import(self):
        """FoodSegmenter class is importable."""
        from nutrisnap.pipeline.segmenter import FoodSegmenter

        assert FoodSegmenter is not None

    def test_pipeline_init_exports(self):
        """Pipeline __init__ exports FoodSegmenter."""
        from nutrisnap.pipeline import FoodSegmenter

        assert FoodSegmenter is not None


class TestFoodSegmenterConfig:
    """Tests for FoodSegmenter configuration handling."""

    def test_missing_config_raises(self):
        """FoodSegmenter raises InferenceError for missing config."""
        with pytest.raises(InferenceError, match="config not found"):
            from nutrisnap.pipeline.segmenter import FoodSegmenter

            FoodSegmenter(config_path="/nonexistent/config.yaml")

    def test_config_loads_yaml(self, tmp_path):
        """FoodSegmenter loads a valid YAML config."""
        config = tmp_path / "test_seg.yaml"
        config.write_text(
            "model:\n"
            "  sam_checkpoint: fake_checkpoint.pth\n"
            "  sam_model_type: vit_h\n"
            "  foodsam_dir: fake_dir\n"
            "inference:\n"
            "  device: cpu\n"
        )
        # Will fail at _validate_setup (checkpoint missing), which is expected
        with pytest.raises(InferenceError, match="not found"):
            from nutrisnap.pipeline.segmenter import FoodSegmenter

            FoodSegmenter(config_path=str(config))


class TestFoodSegmenterSegment:
    """Tests for FoodSegmenter.segment() with mocked SAM."""

    def test_segment_missing_image(self, tmp_path):
        """segment() raises InferenceError for missing image."""
        from nutrisnap.pipeline.segmenter import FoodSegmenter

        # Mock the segmenter to bypass __init__ validation
        with patch.object(FoodSegmenter, "_validate_setup", return_value=None):
            with patch.object(
                FoodSegmenter,
                "_load_config",
                return_value={"vram_management": {"max_image_dim": 1024}},
            ):
                with patch.object(FoodSegmenter, "_resolve_device", return_value="cpu"):
                    seg = FoodSegmenter(config_path=str(tmp_path / "fake_config.yaml"))
                    with pytest.raises(InferenceError, match="not found"):
                        seg.segment(tmp_path / "nonexistent.jpg")


class TestSegmentationError:
    """Tests for SegmentationError exception."""

    def test_segmentation_error_hierarchy(self):
        """SegmentationError is a subclass of InferenceError."""
        from nutrisnap.utils.exceptions import InferenceError, SegmentationError

        assert issubclass(SegmentationError, InferenceError)
