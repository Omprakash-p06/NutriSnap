"""Multi-Food Detection Tests.

Tests for multi-food detection pipeline (YOLOv8 + SAM 2).
"""

# Import test utilities if available
try:
    from conftest import *  # noqa: F401, F403
except Exception:
    pass


class TestMultiFoodDetection:
    """Test suite for multi-food detection components."""

    def test_yolo_imports(self):
        """Test YOLOv8 imports correctly."""
        from nutrisnap.pipeline.multi_food import FOOD_CLASSES, MultiFoodDetector

        assert MultiFoodDetector is not None
        assert len(FOOD_CLASSES) > 0
        assert 53 in FOOD_CLASSES  # pizza is in COCO

    def test_yolo_init(self):
        """Test YOLOv8 can be initialized."""
        from nutrisnap.pipeline.multi_food import MultiFoodDetector

        detector = MultiFoodDetector()
        assert detector is not None
        assert detector.model is not None

    def test_sam2_box_prompt_method_exists(self):
        """Test SAM 2 has segment_with_boxes method."""
        from nutrisnap.pipeline.segmenter import FoodSegmenterSAM2

        assert hasattr(FoodSegmenterSAM2, "segment_with_boxes")

    def test_coordinate_normalization(self):
        """Test coordinate normalization between YOLO and SAM 2."""
        from nutrisnap.pipeline.multi_food import MultiFoodDetector

        # YOLO returns [x1, y1, x2, y2] in pixel coords
        yolo_boxes = [[100, 100, 200, 200]]
        image_size = (640, 480)

        # Normalize to [0, 1] range
        normalized = MultiFoodDetector.normalize_boxes(yolo_boxes, image_size)

        assert len(normalized) == 1
        assert 0.0 <= normalized[0][0] <= 1.0
        assert 0.0 <= normalized[0][1] <= 1.0

    def test_coordinate_denormalization(self):
        """Test denormalization back to pixel coordinates."""
        from nutrisnap.pipeline.multi_food import MultiFoodDetector

        # Normalized boxes
        norm_boxes = [[0.15, 0.2, 0.3, 0.4]]
        image_size = (640, 480)

        # Denormalize
        pixel_boxes = MultiFoodDetector.denormalize_boxes(norm_boxes, image_size)

        assert len(pixel_boxes) == 1
        # x1 = 0.15 * 640 = 96
        # y1 = 0.2 * 480 = 96
        assert 90 <= pixel_boxes[0][0] <= 100
        assert 90 <= pixel_boxes[0][1] <= 100
