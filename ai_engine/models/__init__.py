"""AI Models Package.

Model wrappers for YOLOv8, XGBoost, Depth, and Segmentation.
"""

from ai_engine.models.depth_model import DepthModel
from ai_engine.models.portion_model import PortionModel
from ai_engine.models.segmentation_model import SegmentationModel
from ai_engine.models.yolo_model import YOLOModel

__all__ = ["YOLOModel", "PortionModel", "DepthModel", "SegmentationModel"]
