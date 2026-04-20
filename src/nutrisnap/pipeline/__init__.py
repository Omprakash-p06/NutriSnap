"""NutriSnap pipeline components."""
from nutrisnap.pipeline.segmenter import FoodSegmenter

try:
    from nutrisnap.pipeline.volume import VolumeEstimator
except (ImportError, ModuleNotFoundError):
    # VolumeEstimator requires alphashape/trimesh which might be missing in some environments
    VolumeEstimator = None  # type: ignore

__all__ = ["FoodSegmenter", "VolumeEstimator"]
