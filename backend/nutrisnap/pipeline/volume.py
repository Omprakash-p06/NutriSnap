from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import yaml
from scipy.spatial import ConvexHull
from scipy.stats import skew as scipy_skew

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


class VolumeEstimator:
    """Estimates food volume and area from masked depth data.

    Supports:
    - Point cloud projection using fixed camera intrinsics.
    - Reference surface subtraction.
    - Hybrid Volume Estimation: Convex Hull + Alpha Shape.
    """

    def __init__(self, config_path: str | Path | None = "configs/pipeline/volume.yaml"):
        """Initialize with configuration.

        Args:
            config_path: Path to volume.yaml or None for defaults.
        """
        self.config = self._load_config(config_path)
        self.intrinsics = self.config["intrinsics"]
        self.proc_cfg = self.config["processing"]

    def _load_config(self, config_path: str | Path | None) -> dict:
        """Load YAML configuration."""
        # NOTE: GLPN depth output is normalized to [0, 1], NOT raw metres.
        # min_depth / max_depth here are thresholds in that normalized range.
        _defaults = {
            "intrinsics": {"fx": 617.0, "fy": 617.0, "cx": 320.0, "cy": 240.0},
            "processing": {
                "min_depth": 0.05,  # normalized: discard extreme near pixels
                "max_depth": 0.95,  # normalized: discard extreme far pixels
                "z_ref_default": 0.85,  # fallback normalized z_ref (far background)
                "min_points": 50,  # lowered: small food items still get estimated
                "alpha": 10.0,
                "concavity_threshold": 0.7,
            },
        }
        if config_path is None:
            return _defaults
        path = Path(config_path)
        if not path.exists():
            return _defaults
        with open(path) as f:
            return yaml.safe_load(f)

    def _estimate_z_ref(self, depth: np.ndarray, mask: np.ndarray) -> float:
        """Auto-detect the reference (background/table) plane depth.

        Uses the median of background pixels (outside the food mask) as the
        reference depth. This is critical because GLPN output is normalized to
        [0, 1] and the actual camera distance varies per photo.

        Args:
            depth: (H, W) normalized depth map in [0, 1].
            mask: (H, W) binary food mask (1 = food, 0 = background).

        Returns:
            Estimated reference depth in normalized units.
        """
        bg_pixels = depth[mask == 0]
        # Only use pixels in a plausible background range
        bg_far = bg_pixels[bg_pixels > 0.5]
        if len(bg_far) >= 50:
            z_ref = float(np.median(bg_far))
            logger.debug(
                f"Auto z_ref from {len(bg_far)} background pixels: {z_ref:.3f}"
            )
            return z_ref
        # Fallback to config default
        return self.proc_cfg.get("z_ref_default", 0.85)

    def extract_depth_features(self, depth: np.ndarray, mask: np.ndarray) -> dict:
        """Extract statistical depth features for the PortionCorrector.

        These features are used by the XGBoost corrector to learn systematic
        biases in the volume → mass pipeline.

        Args:
            depth: (H, W) normalized depth map in [0, 1].
            mask: (H, W) binary food mask.

        Returns:
            Dict of scalar features.
        """
        masked_depth = depth[mask > 0]
        if len(masked_depth) < 5:
            return {
                "depth_mean": 0.5,
                "depth_std": 0.0,
                "depth_skew": 0.0,
                "depth_p25": 0.5,
                "depth_p75": 0.5,
                "mask_pixel_ratio": 0.0,
            }
        return {
            "depth_mean": float(np.mean(masked_depth)),
            "depth_std": float(np.std(masked_depth)),
            "depth_skew": float(scipy_skew(masked_depth)),
            "depth_p25": float(np.percentile(masked_depth, 25)),
            "depth_p75": float(np.percentile(masked_depth, 75)),
            "mask_pixel_ratio": float(mask.sum()) / float(mask.size),
        }

    def project_to_pc(self, depth: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Project masked depth pixels into a 3D point cloud.

        NOTE: Since GLPN produces normalized [0, 1] depth (not raw metres),
        the resulting coordinates are in normalized units. Volume computed
        from this point cloud is also in normalized units and must be scaled
        by the density DB to produce a mass estimate. The relative shape of
        the point cloud is what matters, not the absolute scale.

        Args:
            depth: (H, W) float32 normalized depth map [0, 1].
            mask: (H, W) binary mask of the food item.

        Returns:
            (N, 3) float32 point cloud.
        """
        # Get coordinates of masked pixels
        v, u = np.where(mask > 0)
        min_pts = self.proc_cfg.get("min_points", 50)
        if len(v) < min_pts:
            logger.warning(f"Segment too small for volume estimation: {len(v)} points")
            return np.zeros((0, 3), dtype=np.float32)

        z = depth[v, u]

        # Filter out extreme outliers in normalized range (sensor noise artifacts)
        valid = (z >= self.proc_cfg["min_depth"]) & (z <= self.proc_cfg["max_depth"])
        v, u, z = v[valid], u[valid], z[valid]

        if len(z) < min_pts:
            return np.zeros((0, 3), dtype=np.float32)

        # Use normalized pixel coordinates as X, Y (intrinsics optional)
        # Keeps geometry meaningful even when camera intrinsics differ from defaults
        H, W = depth.shape
        x = (u.astype(np.float32) - W / 2.0) / W
        y = (v.astype(np.float32) - H / 2.0) / H

        # Return (N, 3)
        return np.column_stack((x, y, z)).astype(np.float32)

    def get_food_heights(
        self,
        pc: np.ndarray,
        z_ref: Optional[float] = None,
        depth: Optional[np.ndarray] = None,
        mask: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Calculate heights above a reference plane.

        Converts absolute Z (normalized depth from camera) to relative height.
        h = z_ref - z  (larger depth value = farther from camera = lower on table)

        If depth + mask are provided, z_ref is auto-detected from background
        pixels. Otherwise falls back to the supplied z_ref or the config default.

        Args:
            pc: (N, 3) point cloud.
            z_ref: Manual reference depth override.
            depth: Full (H, W) depth map for auto z_ref detection.
            mask: Food mask for auto z_ref detection.

        Returns:
            (N, 3) point cloud where Z is height above reference plane.
        """
        if pc.size == 0:
            return pc

        if z_ref is None:
            if depth is not None and mask is not None:
                z_ref = self._estimate_z_ref(depth, mask)
            else:
                z_ref = self.proc_cfg.get("z_ref_default", 0.85)

        # Clone and modify Z channel
        pc_h = pc.copy()
        pc_h[:, 2] = z_ref - pc[:, 2]

        # Clip negative heights (below reference plane) to 0
        pc_h[:, 2] = np.maximum(pc_h[:, 2], 0)

        return pc_h

    def compute_convex_volume(self, pc: np.ndarray) -> float:
        """Calculate volume using Convex Hull (m^3)."""
        if len(pc) < 4:
            return 0.0

        # Check for co-planarity more robustly
        if np.linalg.matrix_rank(pc - pc.mean(axis=0), tol=1e-5) < 3:
            logger.debug("Point cloud is not 3D enough for ConvexHull")
            return 0.0

        try:
            # Use QJ (joggle) to avoid singular matrix errors with nearly co-planar points
            hull = ConvexHull(pc, qhull_options="QJ")
            return float(hull.volume)
        except Exception as e:
            logger.debug(f"ConvexHull failed: {e}")
            return 0.0

    def compute_concave_volume(self, pc: np.ndarray, alpha: float = 10.0) -> float:
        """Calculate volume using Alpha Shape (m^3)."""
        # Disabled because alphashape is unstable on coplanar points and can infinite loop
        return 0.0

    def estimate_volume(
        self,
        pc: np.ndarray,
        depth: Optional[np.ndarray] = None,
        mask: Optional[np.ndarray] = None,
    ) -> Tuple[float, float, str]:
        """Hybrid volume estimation with auto z_ref.

        Args:
            pc: (N, 3) projected point cloud from project_to_pc().
            depth: Full depth map (for z_ref auto-detection). Optional.
            mask: Food mask (for z_ref auto-detection). Optional.

        Returns:
            (volume_normalized, area_normalized, type_str)
            Note: units are in normalized coordinates (not m³). The downstream
            density-based mass calculation handles unit scaling.
        """
        if pc.size == 0:
            return 0.0, 0.0, "unknown"

        # Apply height transform with auto z_ref
        pc_h = self.get_food_heights(pc, depth=depth, mask=mask)

        # Check for flat point clouds (which cause alphashape infinite loops)
        if np.ptp(pc_h[:, 2]) < 1e-4:
            logger.warning(
                "Point cloud is flat (Z-variance ~ 0). Skipping volume estimation."
            )
            return 0.0, 0.0, "flat"

        # 2D Area
        x_min, x_max = np.min(pc_h[:, 0]), np.max(pc_h[:, 0])
        y_min, y_max = np.min(pc_h[:, 1]), np.max(pc_h[:, 1])
        area = (x_max - x_min) * (y_max - y_min)

        v_ch = self.compute_convex_volume(pc_h)
        v_as = self.compute_concave_volume(pc_h, alpha=self.proc_cfg.get("alpha", 10.0))

        threshold = self.proc_cfg.get("concavity_threshold", 0.7)
        if v_as > 1e-9 and (v_as / v_ch) < threshold:
            return v_as, area, "concave"

        return v_ch, area, "convex"
