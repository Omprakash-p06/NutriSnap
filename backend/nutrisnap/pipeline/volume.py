from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import yaml
from scipy.spatial import ConvexHull

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
        if config_path is None:
            return {
                "intrinsics": {"fx": 617.0, "fy": 617.0, "cx": 320.0, "cy": 240.0},
                "processing": {
                    "min_depth": 0.01,
                    "max_depth": 0.40,
                    "z_ref_default": 0.35,
                    "min_points": 100,
                    "alpha": 10.0,
                    "concavity_threshold": 0.7,
                },
            }
        path = Path(config_path)
        if not path.exists():
            # Fallback for testing or defaults
            return {
                "intrinsics": {"fx": 617.0, "fy": 617.0, "cx": 320.0, "cy": 240.0},
                "processing": {
                    "min_depth": 0.01,
                    "max_depth": 0.40,
                    "z_ref_default": 0.35,
                    "min_points": 100,
                    "alpha": 10.0,
                    "concavity_threshold": 0.7,
                },
            }
        with open(path) as f:
            return yaml.safe_load(f)

    def project_to_pc(self, depth: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Project masked depth pixels into a 3D point cloud (meters).

        Args:
            depth: (H, W) float32 depth map in meters.
            mask: (H, W) binary mask of the food item.

        Returns:
            (N, 3) float32 point cloud in [X, Y, Z] metric space.
        """
        # Get coordinates of masked pixels
        v, u = np.where(mask > 0)
        min_pts = self.proc_cfg.get("min_points", 100)
        if len(v) < min_pts:
            logger.warning(f"Segment too small for volume estimation: {len(v)} points")
            return np.zeros((0, 3), dtype=np.float32)

        z = depth[v, u]

        # Filter points by reliable depth range
        valid = (z >= self.proc_cfg["min_depth"]) & (z <= self.proc_cfg["max_depth"])
        v, u, z = v[valid], u[valid], z[valid]

        if len(z) < min_pts:
            return np.zeros((0, 3), dtype=np.float32)

        # Intrinsic projection
        fx, fy = self.intrinsics["fx"], self.intrinsics["fy"]
        cx, cy = self.intrinsics["cx"], self.intrinsics["cy"]

        x = (u - cx) * z / fx
        y = (v - cy) * z / fy

        # Return (N, 3)
        return np.column_stack((x, y, z)).astype(np.float32)

    def get_food_heights(
        self, pc: np.ndarray, z_ref: Optional[float] = None
    ) -> np.ndarray:
        """Calculate heights above a reference plane (meters).

        Converts absolute Z (distance from camera) to relative height H.
        h = z_ref - z

        Args:
            pc: (N, 3) point cloud.
            z_ref: Reference Z (tabletop). If None, uses config default.

        Returns:
            (N, 3) point cloud where Z is height above reference plane.
        """
        if pc.size == 0:
            return pc

        if z_ref is None:
            z_ref = self.proc_cfg["z_ref_default"]

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
        try:
            hull = ConvexHull(pc)
            return float(hull.volume)
        except Exception as e:
            logger.debug(f"ConvexHull failed: {e}")
            return 0.0

    def compute_concave_volume(self, pc: np.ndarray, alpha: float = 10.0) -> float:
        """Calculate volume using Alpha Shape (m^3)."""
        if len(pc) < 4:
            return 0.0
        try:
            import alphashape

            ashape = alphashape.alphashape(pc, alpha)
            if hasattr(ashape, "volume"):
                return float(ashape.volume)
            if hasattr(ashape, "to_mesh"):
                mesh = ashape.to_mesh()
                return float(mesh.volume)
            return 0.0
        except (ImportError, ModuleNotFoundError):
            logger.error("alphashape not installed. Concave volume estimation failed.")
            return 0.0
        except Exception as e:
            logger.debug(f"AlphaShape failed: {e}")
            return 0.0

    def estimate_volume(self, pc: np.ndarray) -> Tuple[float, float, str]:
        """Hybrid volume estimation.

        Returns:
            (volume_m3, area_m2, type_str)
        """
        if pc.size == 0:
            return 0.0, 0.0, "unknown"

        # 2D Area
        x_min, x_max = np.min(pc[:, 0]), np.max(pc[:, 0])
        y_min, y_max = np.min(pc[:, 1]), np.max(pc[:, 1])
        area_m2 = (x_max - x_min) * (y_max - y_min)

        v_ch = self.compute_convex_volume(pc)
        v_as = self.compute_concave_volume(pc, alpha=self.proc_cfg.get("alpha", 10.0))

        threshold = self.proc_cfg.get("concavity_threshold", 0.7)
        if v_as > 1e-9 and (v_as / v_ch) < threshold:
            return v_as, area_m2, "concave"

        return v_ch, area_m2, "convex"
