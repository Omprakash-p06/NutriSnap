"""Zero-Shot food detection using OWL-ViT.

Allows detecting arbitrary food items using text prompts without retraining.
Acts as a fallback for the YOLOv8 detector.
"""

from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import torch
from PIL import Image
from transformers import OwlViTForObjectDetection, OwlViTProcessor

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


class ZeroShotFoodDetector:
    """Zero-shot object detector using OWL-ViT."""

    def __init__(
        self,
        model_name: str = "google/owlvit-base-patch32",
        device: Optional[str] = None,
        confidence_threshold: float = 0.05,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.confidence_threshold = confidence_threshold

        logger.info(f"Loading OWL-ViT ({model_name}) on {self.device}...")
        self.processor = OwlViTProcessor.from_pretrained(model_name)
        self.model = OwlViTForObjectDetection.from_pretrained(model_name).to(
            self.device
        )
        logger.info("OWL-ViT loaded successfully")

    def detect(
        self,
        image: Union[str, Path, np.ndarray, Image.Image],
        queries: List[str],
        tiled: bool = True,
    ) -> list[dict]:
        """Detect items using text queries.

        Args:
            image: Path, numpy array, or PIL Image.
            queries: List of text prompts (e.g., ["pizza", "biryani", "salad"]).
            tiled: Whether to use tiled inference for high-res images.

        Returns:
            List of detections.
        """
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)

        # Use tiled inference for large images (e.g., > 1500px in any dimension)
        if tiled and (image.width > 1500 or image.height > 1500):
            # Defense-in-depth: Reject extremely large images that bypassed API checks
            if image.width > 6000 or image.height > 6000:
                logger.error(
                    f"Image too large for Zero-Shot ({image.width}x{image.height})"
                )
                return []
            return self._detect_tiled(image, queries)

        # Prepare inputs - ensure we don't downscale too aggressively
        # OwlViTProcessor handles resizing, but we can check if it's possible to keep more detail
        inputs = self.processor(text=[queries], images=image, return_tensors="pt").to(
            self.device
        )

        # Run inference
        with torch.no_grad():
            outputs = self.model(**inputs)

        return self._post_process(outputs, image, queries)

    def _post_process(self, outputs, image, queries) -> list[dict]:
        """Post-process model outputs into detection list."""
        # Log max scores for diagnosis
        logits = outputs.logits[0]  # [num_boxes, num_queries]
        probs = logits.sigmoid()

        max_val = torch.max(probs)
        if max_val > 0.01:  # Only log if there's some signal
            logger.debug(
                f"Tile max score: {max_val:.4f} (threshold: {self.confidence_threshold})"
            )

        # Target image sizes (height, width) to rescale box predictions [batch_size, 2]
        target_sizes = torch.Tensor([image.size[::-1]]).to(self.device)

        if hasattr(self.processor, "post_process_grounded_object_detection"):
            results = self.processor.post_process_grounded_object_detection(
                outputs,
                threshold=self.confidence_threshold,
                target_sizes=target_sizes,
                text_labels=[queries],
            )
        else:
            proc = getattr(self.processor, "image_processor", self.processor)
            results = proc.post_process_object_detection(
                outputs, threshold=self.confidence_threshold, target_sizes=target_sizes
            )

        res = results[0]
        boxes, scores, labels = res["boxes"], res["scores"], res["labels"]
        text_labels = res.get("text_labels", [])

        detections = []
        for idx, (box, score, label) in enumerate(zip(boxes, scores, labels)):
            box_coords = [int(val) for val in box.tolist()]

            if text_labels and idx < len(text_labels):
                query = text_labels[idx]
            else:
                query = queries[label.item()]

            detections.append(
                {
                    "label": query,
                    "bbox_xyxy": box_coords,
                    "confidence": float(score),
                    "source": "owl_vit",
                }
            )

        return detections

    def _detect_tiled(
        self,
        image: Image.Image,
        queries: List[str],
        tile_size: int = 800,
        overlap: int = 200,
    ) -> list[dict]:
        """Run inference on tiles and merge results."""
        width, height = image.size
        all_detections = []

        # Calculate tile coordinates
        x_starts = range(0, max(1, width - overlap), tile_size - overlap)
        y_starts = range(0, max(1, height - overlap), tile_size - overlap)

        logger.info(f"Tiled inference: {len(x_starts)}x{len(y_starts)} tiles")

        for y in y_starts:
            for x in x_starts:
                # Extract tile
                box = (x, y, min(x + tile_size, width), min(y + tile_size, height))
                tile = image.crop(box)

                # Inference on tile
                inputs = self.processor(
                    text=[queries], images=tile, return_tensors="pt"
                ).to(self.device)
                with torch.no_grad():
                    outputs = self.model(**inputs)

                tile_dets = self._post_process(outputs, tile, queries)

                # Offset coordinates back to original image
                for det in tile_dets:
                    tx1, ty1, tx2, ty2 = det["bbox_xyxy"]
                    det["bbox_xyxy"] = [tx1 + x, ty1 + y, tx2 + x, ty2 + y]
                    all_detections.append(det)

        if not all_detections:
            return []

        # Simple NMS to merge overlapping detections
        return self._apply_nms(all_detections)

    def _apply_nms(
        self, detections: list[dict], iou_threshold: float = 0.5
    ) -> list[dict]:
        """Apply Non-Maximum Suppression to merged detections."""
        if not detections:
            return []

        # Sort by confidence descending
        sorted_dets = sorted(detections, key=lambda x: x["confidence"], reverse=True)
        keep = []

        while sorted_dets:
            best = sorted_dets.pop(0)
            keep.append(best)

            remaining = []
            for det in sorted_dets:
                if (
                    self._calculate_iou(best["bbox_xyxy"], det["bbox_xyxy"])
                    < iou_threshold
                ):
                    remaining.append(det)
            sorted_dets = remaining

        return keep

    @staticmethod
    def _calculate_iou(box1: list[int], box2: list[int]) -> float:
        """Calculate Intersection over Union of two boxes."""
        x1, y1, x2, y2 = box1
        x3, y3, x4, y4 = box2

        inter_x1 = max(x1, x3)
        inter_y1 = max(y1, y3)
        inter_x2 = min(x2, x4)
        inter_y2 = min(y2, y4)

        inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)

        area1 = (x2 - x1) * (y2 - y1)
        area2 = (x4 - x3) * (y4 - y3)

        union_area = area1 + area2 - inter_area
        if union_area == 0:
            return 0

        return inter_area / union_area

    def unload(self) -> None:
        """Free memory."""
        del self.model
        del self.processor
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("OWL-ViT unloaded")
