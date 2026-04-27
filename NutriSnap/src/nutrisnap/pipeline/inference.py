"""Multi-Food Inference Pipeline for NutriSnap.

Orchestrates the complete multi-food detection and validation pipeline:
1. YOLOv8 (detection) -> SAM 2 (segmentation with boxes) -> GLPN (depth) -> MultiFoodMerger (volume/nutrition) -> LLMValidator (validation)

Designed for sequential execution to respect the 4GB VRAM limit (RTX 3050).
Target latency: <3s per request with LLM overhead.

Usage::

    from nutrisnap.pipeline.inference import MultiFoodInferencePipeline

    pipeline = MultiFoodInferencePipeline()
    result = pipeline.predict("path/to/meal.jpg")
    
    # result = {
    #     "items": [{"label": "pizza", "calories": 500, ...}, ...],
    #     "total_calories": 850,
    #     "validation_summary": {"is_valid": True, "reasoning": "..."}
    # }
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

import cv2
import numpy as np
import numpy.typing as npt
import torch

from nutrisnap.pipeline.multi_food import MultiFoodDetector
from nutrisnap.pipeline.segmenter import FoodSegmenterSAM2
from nutrisnap.pipeline.depth import DepthEstimatorGLPN
from nutrisnap.pipeline.merger import MultiFoodMerger, MergedPrediction
from nutrisnap.verification.llm_validator import LLMValidator, ValidationResult
from nutrisnap.utils.logger import get_logger
from nutrisnap.utils.exceptions import InferenceError

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    """Result from multi-food inference pipeline."""
    
    # Itemized predictions from merger
    items: list[dict[str, Any]]
    merged_prediction: MergedPrediction
    
    # Aggregated totals
    total_calories: float
    total_mass_g: float
    total_protein: float
    total_carbs: float
    total_fat: float
    
    # LLM validation results
    validation_result: ValidationResult
    
    # Metadata
    latency_seconds: float
    item_count: int
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        items_list = []
        for item in self.items:
            items_list.append({
                "label": item.label,
                "confidence": item.confidence,
                "volume_cm3": round(item.volume_cm3, 1),
                "mass_g": round(item.mass_g, 1),
                "calories": round(item.total_calories, 1),
                "protein": round(item.total_protein, 1),
                "carbs": round(item.total_carbs, 1),
                "fat": round(item.total_fat, 1),
            })
        
        return {
            "items": items_list,
            "total_calories": round(self.total_calories, 1),
            "total_mass_g": round(self.total_mass_g, 1),
            "total_protein": round(self.total_protein, 1),
            "total_carbs": round(self.total_carbs, 1),
            "total_fat": round(self.total_fat, 1),
            "validation_summary": {
                "is_valid": self.validation_result.is_valid,
                "reasoning": self.validation_result.reasoning,
                "llm_reasoning": self.validation_result.reasoning,
                "corrections": self.validation_result.corrections,
            },
            "latency_seconds": round(self.latency_seconds, 2),
            "item_count": self.item_count,
        }


class MultiFoodInferencePipeline:
    """Multi-food detection and validation pipeline orchestrator.
    
    Pipeline stages (sequential for VRAM management):
    1. YOLOv8: Detect food bounding boxes
    2. SAM 2: Segment each detection (box-prompted)
    3. GLPN: Estimate depth for volume
    4. MultiFoodMerger: Compute volume -> mass -> nutrition
    5. LLMValidator: Validate realism (async)
    
    All models are sequentially executed and unloaded between stages
    to fit within 4GB VRAM envelope.
    """
    
    # VRAM thresholds
    MIN_VRAM_GB = 2.0
    MAX_IMAGE_DIM = 1024
    
    def __init__(
        self,
        config_dir: Optional[Path | str] = None,
        checkpoint_dir: Optional[Path | str] = None,
        device: Optional[str] = None,
        enable_llm_validation: bool = True,
    ):
        """Initialize the multi-food inference pipeline.
        
        Args:
            config_dir: Path to config directory (default: configs/)
            checkpoint_dir: Path to model checkpoints (default: models/)
            device: Override device ('cuda', 'cpu', or None for auto)
            enable_llm_validation: Enable LLM validation (default: True)
        """
        self.config_dir = Path(config_dir) if config_dir else Path("configs")
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else Path("models")
        
        # Resolve device
        self.device_str = self._resolve_device(device)
        self.device = torch.device(self.device_str)
        
        self.enable_llm_validation = enable_llm_validation
        
        # Initialize components (lazy loading for VRAM management)
        self._detector: Optional[MultiFoodDetector] = None
        self._segmenter: Optional[FoodSegmenterSAM2] = None
        self._depth_estimator: Optional[DepthEstimatorGLPN] = None
        self._merger: Optional[MultiFoodMerger] = None
        self._llm_validator: Optional[LLMValidator] = None
        
        logger.info(f"MultiFoodInferencePipeline initialized (device: {self.device_str}, llm: {enable_llm_validation})")
    
    def _resolve_device(self, device_override: Optional[str]) -> str:
        """Resolve compute device with auto-detection and VRAM check."""
        if device_override and device_override != "auto":
            return device_override
        
        if not torch.cuda.is_available():
            logger.warning("CUDA not available - using CPU")
            return "cpu"
        
        # Check VRAM
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        logger.info(f"GPU: {torch.cuda.get_device_name(0)} ({vram_gb:.1f} GB)")
        
        if vram_gb < self.MIN_VRAM_GB:
            logger.warning(f"Low VRAM ({vram_gb:.1f} GB) - falling back to CPU")
            return "cpu"
        
        return "cuda"
    
    @property
    def detector(self) -> MultiFoodDetector:
        """Get or create YOLOv8 detector (loads on demand)."""
        if self._detector is None:
            logger.info("Loading YOLOv8 detector...")
            self._detector = MultiFoodDetector(device=self.device_str)
        return self._detector
    
    @property
    def segmenter(self) -> FoodSegmenterSAM2:
        """Get or create SAM 2 segmenter (loads on demand)."""
        if self._segmenter is None:
            logger.info("Loading SAM 2 segmenter...")
            self._segmenter = FoodSegmenterSAM2(device=self.device_str)
        return self._segmenter
    
    @property
    def depth_estimator(self) -> DepthEstimatorGLPN:
        """Get or create GLPN depth estimator (loads on demand)."""
        if self._depth_estimator is None:
            logger.info("Loading GLPN depth estimator...")
            volume_config = self.config_dir / "pipeline" / "volume.yaml"
            self._depth_estimator = DepthEstimatorGLPN(
                config_path=str(volume_config) if volume_config.exists() else None,
                device=self.device_str
            )
        return self._depth_estimator
    
    @property
    def merger(self) -> MultiFoodMerger:
        """Get or create MultiFoodMerger (loads on demand)."""
        if self._merger is None:
            logger.info("Loading MultiFoodMerger...")
            volume_config = self.config_dir / "pipeline" / "volume.yaml"
            self._merger = MultiFoodMerger(
                volume_config=str(volume_config) if volume_config.exists() else None
            )
        return self._merger
    
    @property
    def llm_validator(self) -> Optional[LLMValidator]:
        """Get or create LLM validator (loads on demand)."""
        if not self.enable_llm_validation:
            return None
        if self._llm_validator is None:
            logger.info("Loading LLM validator...")
            self._llm_validator = LLMValidator()
        return self._llm_validator
    
    def _unload_all(self) -> None:
        """Unload all models from VRAM to free memory between stages.
        
        Sequential execution strategy to respect 4GB VRAM limit.
        Each model is unloaded before the next is loaded.
        """
        for component_name in ["detector", "segmenter", "depth_estimator"]:
            component = getattr(self, f"_{component_name}", None)
            if component and hasattr(component, "unload"):
                try:
                    component.unload()
                except Exception as e:
                    logger.warning(f"Failed to unload {component_name}: {e}")
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def _sequential_execute(self) -> None:
        """Alias for _unload_all - sequential execution strategy for VRAM management."""
        return self._unload_all()
    
    def _preprocess_image(
        self,
        image: Union[str, Path, np.ndarray]
    ) -> tuple[np.ndarray, tuple[int, int]]:
        """Preprocess image for pipeline.
        
        Args:
            image: Path to image or numpy array (RGB).
            
        Returns:
            Tuple of (RGB image array, original shape).
        """
        if isinstance(image, (str, Path)):
            img_bgr = cv2.imread(str(image))
            if img_bgr is None:
                raise InferenceError(f"Failed to read image: {image}")
            image_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
        
        original_shape = image_rgb.shape[:2]
        
        # Resize if too large for VRAM
        h, w = original_shape
        if max(h, w) > self.MAX_IMAGE_DIM:
            scale = self.MAX_IMAGE_DIM / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            image_rgb = cv2.resize(image_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
            logger.info(f"Resized image from ({h},{w}) to ({new_h},{new_w}) for VRAM")
        
        return image_rgb, original_shape
    
    def predict(
        self,
        image: Union[str, Path, np.ndarray],
        max_detections: int = 10,
    ) -> PipelineResult:
        """Run the full multi-food inference pipeline.
        
        Args:
            image: Path to meal image or RGB numpy array.
            max_detections: Maximum number of food detections.
            
        Returns:
            PipelineResult with itemized predictions and validation.
        """
        start_time = time.time()
        
        # Stage 1: Preprocess image
        image_rgb, original_shape = self._preprocess_image(image)
        
        # Stage 2: YOLOv8 detection
        logger.info("Stage 1/4: YOLOv8 detection...")
        detections = self.detector.detect_food_only(image_rgb, max_detections=max_detections)
        
        if not detections:
            logger.warning("No food detections - returning empty result")
            return self._empty_result(start_time)
        
        # Extract bounding boxes for SAM 2
        boxes = [d["box"] for d in detections]
        # Normalize boxes for SAM 2 prompts
        normalized_boxes = MultiFoodDetector.normalize_boxes(boxes, (image_rgb.shape[1], image_rgb.shape[0]))
        
        # Stage 3: SAM 2 segmentation with box prompts
        # First unload detector to free VRAM
        self._unload_all()
        
        logger.info("Stage 2/4: SAM 2 segmentation...")
        seg_result = self.segmenter.segment_with_boxes(image_rgb, normalized_boxes)
        masks = seg_result["masks"]
        scores = seg_result["scores"]
        
        if not masks:
            logger.warning("No segmentation masks - returning empty result")
            return self._empty_result(start_time)
        
        # Stage 4: GLPN depth estimation
        # Unload segmenter
        self._unload_all()
        
        logger.info("Stage 3/4: GLPN depth estimation...")
        depth_map = self.depth_estimator.estimate(image_rgb)
        
        # Stage 5: MultiFoodMerger - volume & nutrition
        # Unload depth estimator
        self._unload_all()
        
        logger.info("Stage 4/4: MultiFoodMerger volume estimation...")
        
        # Map labels/scores from detections to masks
        merged_detections = []
        for i, det in enumerate(detections[:len(masks)]):
            merged_detections.append({
                "label": det.get("label", f"food_{i}"),
                "confidence": det.get("confidence", scores[i] if i < len(scores) else 0.5)
            })
        
        merged_result = self.merger.merge_with_overlap_check(
            merged_detections,
            masks,
            depth_map
        )
        
        # Stage 6: LLM validation (async)
        validation_result: Optional[ValidationResult] = None
        if self.enable_llm_validation and self.llm_validator is not None:
            logger.info("Stage 5/5: LLM validation...")
            
            # Prepare items JSON for validation
            items_json = []
            for item in merged_result.items:
                items_json.append({
                    "label": item.label,
                    "volume_cm3": round(item.volume_cm3, 1),
                    "calories": round(item.total_calories, 1),
                })
            
            import asyncio
            try:
                validation_result = asyncio.get_event_loop().run_until_complete(
                    self.llm_validator.validate_meal(
                        items_json,
                        merged_result.total_calories,
                        None  # No image path needed for validation
                    )
                )
            except RuntimeError:
                # If no event loop, create one
                validation_result = asyncio.run(
                    self.llm_validator.validate_meal(
                        items_json,
                        merged_result.total_calories,
                        None
                    )
                )
        
        # Calculate latency
        latency = time.time() - start_time
        
        # Build result
        result = PipelineResult(
            items=merged_result.items,
            merged_prediction=merged_result,
            total_calories=merged_result.total_calories,
            total_mass_g=merged_result.total_mass_g,
            total_protein=merged_result.total_protein,
            total_carbs=merged_result.total_carbs,
            total_fat=merged_result.total_fat,
            validation_result=validation_result or ValidationResult(
                is_valid=True,
                reasoning="Validation skipped",
                corrections=[],
                final_items=[]
            ),
            latency_seconds=latency,
            item_count=merged_result.item_count,
        )
        
        logger.info(f"Pipeline complete: {result.item_count} items, {result.total_calories:.1f} kcal, {latency:.2f}s")
        
        return result
    
    def _empty_result(self, start_time: float) -> PipelineResult:
        """Create an empty result for no detections."""
        from nutrisnap.pipeline.merger import FoodItem
        from nutrisnap.verification.llm_validator import ValidationResult
        
        latency = time.time() - start_time
        
        return PipelineResult(
            items=[],
            merged_prediction=MergedPrediction.from_items([]),
            total_calories=0.0,
            total_mass_g=0.0,
            total_protein=0.0,
            total_carbs=0.0,
            total_fat=0.0,
            validation_result=ValidationResult(
                is_valid=True,
                reasoning="No food detected",
                corrections=[],
                final_items=[]
            ),
            latency_seconds=latency,
            item_count=0,
        )


# Convenience function for quick predictions
def predict_multi(
    image: Union[str, Path],
    **kwargs
) -> dict[str, Any]:
    """Quick multi-food prediction.
    
    Args:
        image: Path to meal image.
        **kwargs: Additional pipeline args.
        
    Returns:
        Dictionary with pipeline results.
    """
    pipeline = MultiFoodInferencePipeline()
    result = pipeline.predict(image, **kwargs)
    return result.to_dict()