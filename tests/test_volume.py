"""Tests for VolumeEstimator pipeline component."""

import numpy as np
import pytest

from nutrisnap.pipeline.volume import VolumeEstimator


class TestVolumeEstimatorInit:
    """Tests for VolumeEstimator initialization."""

    def test_import_works(self):
        """VolumeEstimator is importable."""
        from nutrisnap.pipeline.volume import VolumeEstimator

        assert VolumeEstimator is not None

    def test_init_with_defaults(self):
        """Init works even if config file is missing (using internal defaults)."""
        est = VolumeEstimator(config_path="/nonexistent/config.yaml")
        assert est.intrinsics["fx"] == 617.0


class TestPointCloudProjection:
    """Tests for 3D point cloud projection logic."""

    @pytest.fixture
    def estimator(self):
        return VolumeEstimator(config_path="/nonexistent/config.yaml")

    def test_projection_shape(self, estimator):
        """Projected PC has correct (N, 3) shape."""
        # Mock depth: 100x100 at 0.3m
        depth = np.full((100, 100), 0.3, dtype=np.float32)
        # Mock mask: 10x10 square in the center
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[45:55, 45:55] = 255

        pc = estimator.project_to_pc(depth, mask)
        assert pc.shape == (100, 3)
        assert pc.dtype == np.float32

    def test_projection_metric_scale(self, estimator):
        """A 10-pixel wide object at 0.3m projects to expected metric width."""
        # cx=320, fx=617.
        # Width in pixels = 10
        # Metric width = (W_px_delta * Z) / fx
        # pixel indices 5 to 109 -> delta = 104
        expected_width = (104 * 0.3) / 617.0

        depth = np.full((120, 120), 0.3, dtype=np.float32)
        mask = np.zeros((120, 120), dtype=np.uint8)
        mask[50, 5:110] = 255  # 105 pixels horizontally

        pc = estimator.project_to_pc(depth, mask)
        # X is the first column
        width_m = np.max(pc[:, 0]) - np.min(pc[:, 0])

        assert pytest.approx(width_m, abs=1e-5) == expected_width

    def test_filter_invalid_depth(self, estimator):
        """Too close or too far points are filtered out."""
        depth = np.full((100, 100), 0.0, dtype=np.float32)  # Invalid (too close)
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[45:55, 45:55] = 255

        pc = estimator.project_to_pc(depth, mask)
        assert len(pc) == 0

    def test_height_mapping(self, estimator):
        """Heights are correctly calculated relative to z_ref."""
        # pc: N points at Z = 0.25. z_ref = 0.35.
        # Height should be 0.10.
        pc = np.array([[0, 0, 0.25], [0, 0.01, 0.25]], dtype=np.float32)
        pc_h = estimator.get_food_heights(pc, z_ref=0.35)

        assert np.allclose(pc_h[:, 2], 0.10)
        # Verify X and Y are unchanged
        assert np.allclose(pc_h[:, :2], pc[:, :2])

    def test_height_clipping(self, estimator):
        """Points below the reference plane (z > z_ref) are clipped to 0 height."""
        # pc: Z = 0.40. z_ref = 0.35. Height = -0.05 -> clipped to 0.
        pc = np.array([[0, 0, 0.40]], dtype=np.float32)
        pc_h = estimator.get_food_heights(pc, z_ref=0.35)

        assert pc_h[0, 2] == 0.0


class TestHybridVolume:
    """Tests for Convex Hull, Alpha Shape, and Hybrid Switching."""

    @pytest.fixture
    def estimator(self):
        return VolumeEstimator(config_path="/nonexistent/config.yaml")

    def test_convex_hull_cube(self, estimator):
        """A 10x10x10cm cube has ~1000cm^3 volume."""
        # Create 8 corners of a 10cm cube (0.1m)
        points = np.array(
            [
                [0, 0, 0],
                [0.1, 0, 0],
                [0, 0.1, 0],
                [0, 0, 0.1],
                [0.1, 0.1, 0],
                [0.1, 0, 0.1],
                [0, 0.1, 0.1],
                [0.1, 0.1, 0.1],
            ],
            dtype=np.float32,
        )
        vol = estimator.compute_convex_volume(points)
        # 0.1 * 0.1 * 0.1 = 0.001 m^3
        assert pytest.approx(vol, abs=1e-6) == 0.001

    def test_alpha_shape_cube(self, estimator):
        """Alpha shape should also capture cube volume."""
        points = np.array(
            [
                [0, 0, 0],
                [0.1, 0, 0],
                [0, 0.1, 0],
                [0, 0, 0.1],
                [0.1, 0.1, 0],
                [0.1, 0, 0.1],
                [0, 0.1, 0.1],
                [0.1, 0.1, 0.1],
            ],
            dtype=np.float32,
        )
        vol = estimator.compute_concave_volume(points, alpha=10.0)
        assert vol > 0.0005  # Should be close to 0.001

    def test_estimate_volume_switcher(self, estimator):
        """Estimate volume returns volume, area, and type."""
        # Cube (Convex)
        points = np.random.rand(100, 3).astype(np.float32) * 0.1
        vol, area, vtype = estimator.estimate_volume(points)

        assert vol > 0
        assert area > 0
        assert vtype in ["convex", "concave"]
