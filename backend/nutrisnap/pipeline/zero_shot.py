"""Zero-Shot food detection using OWL-ViT.

Allows detecting arbitrary food items using text prompts without retraining.
Acts as a fallback for the YOLOv8 detector.
"""

from typing import Optional, Union, List
from pathlib import Path

import torch
import numpy as np
from PIL import Image
from transformers import OwlViTProcessor, OwlViTForObjectDetection

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

class ZeroShotFoodDetector:
    """Zero-shot object detector using OWL-ViT."""

    def __init__(
        self,
        model_name: str = "google/owlvit-base-patch32",
        device: Optional[str] = None,
        confidence_threshold: float = 0.1,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.confidence_threshold = confidence_threshold
        
        logger.info(f"Loading OWL-ViT ({model_name}) on {self.device}...")
        self.processor = OwlViTProcessor.from_pretrained(model_name)
        self.model = OwlViTForObjectDetection.from_pretrained(model_name).to(self.device)
        logger.info("OWL-ViT loaded successfully")

    def detect(
        self,
        image: Union[str, Path, np.ndarray, Image.Image],
        queries: List[str],
    ) -> list[dict]:
        """Detect items using text queries.
        
        Args:
            image: Path, numpy array, or PIL Image.
            queries: List of text prompts (e.g., ["pizza", "biryani", "salad"]).
            
        Returns:
            List of detections.
        """
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)

        # Prepare inputs
        inputs = self.processor(text=[queries], images=image, return_tensors="pt").to(self.device)
        
        # Run inference
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Target image sizes (height, width) to rescale box predictions [batch_size, 2]
        target_sizes = torch.Tensor([image.size[::-1]]).to(self.device)
        
        # Convert outputs (bounding boxes and class logits) to COCO API
        # In newer transformers versions, OwlViTProcessor uses post_process_grounded_object_detection
        if hasattr(self.processor, "post_process_grounded_object_detection"):
            results = self.processor.post_process_grounded_object_detection(
                outputs, 
                threshold=self.confidence_threshold, 
                target_sizes=target_sizes,
                text_labels=[queries]
            )
        else:
            # Fallback for older versions or if it's on image_processor
            proc = getattr(self.processor, "image_processor", self.processor)
            results = proc.post_process_object_detection(outputs, threshold=self.confidence_threshold, target_sizes=target_sizes)

        i = 0  # Only one image
        res = results[i]
        boxes, scores, labels = res["boxes"], res["scores"], res["labels"]
        text_labels = res.get("text_labels", [])

        detections = []
        for idx, (box, score, label) in enumerate(zip(boxes, scores, labels)):
            box_coords = [int(val) for val in box.tolist()]
            
            if text_labels and idx < len(text_labels):
                query = text_labels[idx]
            else:
                query = queries[label.item()]

            detections.append({
                "label": query,
                "box": box_coords,
                "score": float(score),
                "source": "owl_vit"
            })

        logger.info(f"OWL-ViT detected {len(detections)} items for queries: {queries}")
        return detections

    def unload(self) -> None:
        """Free memory."""
        del self.model
        del self.processor
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("OWL-ViT unloaded")
