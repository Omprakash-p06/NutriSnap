"""SequentialOrchestrator: Load-Run-Unload pipeline for VRAM-constrained environments.

Manages the full multi-food inference pipeline on a single 4GB GPU by
running each stage sequentially and releasing GPU memory between stages.
"""

from __future__ import annotations

import gc
import time
from dataclasses import dataclass, field
from typing import Any

from loguru import logger


@dataclass
class PipelineResult:
    """Unified result from the multi-food pipeline."""

    items: list[dict[str, Any]] = field(default_factory=list)
    total_calories: float = 0.0
    total_mass_g: float = 0.0
    total_protein: float = 0.0
    total_carbs: float = 0.0
    total_fat: float = 0.0
    total_fiber: float = 0.0
    total_saturated_fat: float = 0.0
    total_sugars: float = 0.0
    validation_summary: dict[str, Any] = field(
        default_factory=lambda: {"is_valid": True, "reasoning": "OK", "corrections": []}
    )
    latency_seconds: float = 0.0
    item_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": self.items,
            "total_calories": self.total_calories,
            "total_mass_g": self.total_mass_g,
            "total_protein": self.total_protein,
            "total_carbs": self.total_carbs,
            "total_fat": self.total_fat,
            "total_fiber": self.total_fiber,
            "total_saturated_fat": self.total_saturated_fat,
            "total_sugars": self.total_sugars,
            "validation_summary": self.validation_summary,
            "latency_seconds": self.latency_seconds,
            "item_count": self.item_count,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Mock (CI / no-GPU) implementation
# ─────────────────────────────────────────────────────────────────────────────


class _MockOrchestrator:
    """Returns plausible-looking mock results without touching the GPU.

    Uses a hash of the image file's size and modification time to
    deterministically vary the returned food label, so different uploaded
    images produce different results instead of always returning the same
    hardcoded value.
    """

    # Pool of realistic food items with plausible macros
    _FOOD_POOL = [
        {
            "label": "Grilled Chicken Salad",
            "confidence": 0.88,
            "volume_cm3": 380.0,
            "mass_g": 300.0,
            "calories": 320.0,
            "protein": 35.0,
            "carbs": 18.0,
            "fat": 11.0,
            "fiber": 4.5,
            "saturated_fat": 2.5,
            "sugars": 5.0,
        },
        {
            "label": "Margherita Pizza",
            "confidence": 0.92,
            "volume_cm3": 600.0,
            "mass_g": 450.0,
            "calories": 800.0,
            "protein": 30.0,
            "carbs": 90.0,
            "fat": 32.0,
            "fiber": 3.0,
            "saturated_fat": 14.0,
            "sugars": 8.0,
        },
        {
            "label": "Egg Fried Rice",
            "confidence": 0.85,
            "volume_cm3": 500.0,
            "mass_g": 400.0,
            "calories": 620.0,
            "protein": 18.0,
            "carbs": 80.0,
            "fat": 20.0,
            "fiber": 2.0,
            "saturated_fat": 4.0,
            "sugars": 3.0,
        },
        {
            "label": "Dal Tadka with Roti",
            "confidence": 0.87,
            "volume_cm3": 450.0,
            "mass_g": 380.0,
            "calories": 490.0,
            "protein": 22.0,
            "carbs": 70.0,
            "fat": 10.0,
            "fiber": 9.0,
            "saturated_fat": 2.0,
            "sugars": 4.0,
        },
        {
            "label": "Caesar Salad",
            "confidence": 0.91,
            "volume_cm3": 350.0,
            "mass_g": 280.0,
            "calories": 380.0,
            "protein": 14.0,
            "carbs": 20.0,
            "fat": 27.0,
            "fiber": 3.0,
            "saturated_fat": 6.0,
            "sugars": 4.0,
        },
        {
            "label": "Vegetable Stir Fry",
            "confidence": 0.83,
            "volume_cm3": 420.0,
            "mass_g": 330.0,
            "calories": 280.0,
            "protein": 8.0,
            "carbs": 35.0,
            "fat": 10.0,
            "fiber": 7.0,
            "saturated_fat": 1.5,
            "sugars": 12.0,
        },
        {
            "label": "Beef Burger",
            "confidence": 0.94,
            "volume_cm3": 550.0,
            "mass_g": 420.0,
            "calories": 750.0,
            "protein": 38.0,
            "carbs": 55.0,
            "fat": 38.0,
            "fiber": 3.0,
            "saturated_fat": 14.0,
            "sugars": 10.0,
        },
        {
            "label": "Sushi Platter",
            "confidence": 0.89,
            "volume_cm3": 400.0,
            "mass_g": 340.0,
            "calories": 480.0,
            "protein": 24.0,
            "carbs": 72.0,
            "fat": 8.0,
            "fiber": 2.0,
            "saturated_fat": 1.5,
            "sugars": 12.0,
        },
        {
            "label": "Pasta Arrabbiata",
            "confidence": 0.86,
            "volume_cm3": 500.0,
            "mass_g": 390.0,
            "calories": 580.0,
            "protein": 20.0,
            "carbs": 85.0,
            "fat": 14.0,
            "fiber": 5.0,
            "saturated_fat": 3.0,
            "sugars": 7.0,
        },
        {
            "label": "Oatmeal with Berries",
            "confidence": 0.90,
            "volume_cm3": 300.0,
            "mass_g": 250.0,
            "calories": 360.0,
            "protein": 10.0,
            "carbs": 65.0,
            "fat": 6.0,
            "fiber": 7.0,
            "saturated_fat": 1.0,
            "sugars": 18.0,
        },
    ]

    _HEALTH_GRADES: dict[str, dict] = {
        "Grilled Chicken Salad": {"grade": "A", "summary": "Excellent protein-to-calorie ratio"},
        "Margherita Pizza": {"grade": "C", "summary": "High carbs; moderate nutrition"},
        "Egg Fried Rice": {"grade": "C", "summary": "Balanced but calorie-dense"},
        "Dal Tadka with Roti": {"grade": "A", "summary": "High fiber, plant-based protein"},
        "Caesar Salad": {"grade": "B", "summary": "Good greens, watch fat content"},
        "Vegetable Stir Fry": {"grade": "A", "summary": "Low calorie, high micronutrients"},
        "Beef Burger": {"grade": "D", "summary": "High saturated fat and calories"},
        "Sushi Platter": {"grade": "B", "summary": "Lean protein, high sodium typical"},
        "Pasta Arrabbiata": {"grade": "B", "summary": "Good carbs, moderate macros"},
        "Oatmeal with Berries": {"grade": "A", "summary": "High fiber, steady energy release"},
    }

    def _pick_food(self, image_path: str) -> dict:
        """Deterministically pick a food from the pool using image metadata hash.

        Hashes the image path + file size + mtime so that genuinely different
        images (even when saved to the same temp filename) return different foods.
        """
        import hashlib
        import os

        h = hashlib.md5()
        h.update(image_path.encode())
        try:
            stat = os.stat(image_path)
            h.update(str(stat.st_size).encode())
            h.update(str(int(stat.st_mtime * 1000)).encode())
        except OSError:
            pass

        idx = int(h.hexdigest(), 16) % len(self._FOOD_POOL)
        return dict(self._FOOD_POOL[idx])  # return a copy

    def predict(self, image_path: str) -> PipelineResult:
        logger.debug(f"MockOrchestrator.predict({image_path})")
        item = self._pick_food(image_path)
        label = item["label"]
        grade_info = self._HEALTH_GRADES.get(label, {"grade": "B", "summary": "Balanced meal"})

        return PipelineResult(
            items=[item],
            total_calories=item["calories"],
            total_mass_g=item["mass_g"],
            total_protein=item["protein"],
            total_carbs=item["carbs"],
            total_fat=item["fat"],
            total_fiber=item["fiber"],
            total_saturated_fat=item["saturated_fat"],
            total_sugars=item["sugars"],
            validation_summary={
                "is_valid": True,
                "reasoning": f"Mock prediction (demo mode) — {label} detected",
                "corrections": [],
                "health_score": grade_info,
            },
            latency_seconds=0.05,
            item_count=1,
        )

    def teardown(self) -> None:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Real (GPU) implementation
# ─────────────────────────────────────────────────────────────────────────────


class _RealOrchestrator:
    """
    Sequential Load-Run-Unload orchestrator.

    Each stage (Detector → Segmenter → Depth → Merger → Validator) loads its
    model, runs inference, then calls .unload() / del + empty_cache before the
    next stage starts. Peak VRAM stays well under 4 GB.
    """

    def __init__(self, device: str = "cuda") -> None:
        self.device = device
        logger.info(f"RealOrchestrator created (device={device})")

    @staticmethod
    def _free_gpu() -> None:
        import torch

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def predict(self, image_path: str) -> PipelineResult:
        t0 = time.perf_counter()
        logger.info(f"Pipeline start: {image_path}")

        # ── Stage 0: Pre-processing (Enhancement) ────────────────────────────
        try:
            from nutrisnap.pipeline.preprocessor import ImagePreprocessor
            
            preprocessor = ImagePreprocessor()
            # Enhance image and use the enhanced version for the rest of the pipeline
            original_image_path = image_path
            image_path = preprocessor.preprocess_for_pipeline(image_path)
            logger.info(f"Using enhanced image: {image_path}")
        except Exception as exc:
            logger.warning(f"Pre-processing failed: {exc}")
            # Fallback to original image if pre-processing fails

        # ── Stage 1: Detection (YOLOv8) ──────────────────────────────────────
        detections: list[dict] = []
        try:
            from nutrisnap.pipeline.multi_food import MultiFoodDetector, LIKELY_FOOD_CLASSES
            import cv2
            import numpy as np
            
            # Quick quality check for black/corrupted images
            img_test = cv2.imread(image_path)
            if img_test is not None and np.mean(img_test) < 1.0:
                logger.warning(f"Image {image_path} appears to be black or extremely dark. Detection may fail.")
            
            import os
            # Check for specialized food model weights
            specialized_weights = os.path.join("models", "food_specialized_yolov8.pt")
            model_to_use = specialized_weights if os.path.exists(specialized_weights) else "yolov8n.pt"

            detector = MultiFoodDetector(model_name=model_to_use, device=self.device)
            # Use higher imgsz for better detection on high-res images
            raw_detections = detector.detect(image_path, imgsz=1280)
            
            # Filter for food items with decent confidence
            detections = [d for d in raw_detections if d.get("class_id") in LIKELY_FOOD_CLASSES and d.get("confidence", 0) > 0.5]
            food_labels = [f"{d.get('label')} ({d.get('confidence', 0):.2f})" for d in detections]
            
            logger.info(f"YOLOv8 ({model_to_use}) detected {len(raw_detections)} total items, {len(detections)} high-confidence food items: {food_labels}")
            
            if len(raw_detections) > 0 and len(detections) == 0:
                logger.info("YOLO found no high-confidence food. Proceeding to Zero-Shot fallback.")
                detections = [] # Trigger fallback logic below            
            if hasattr(detector, "unload"):
                detector.unload()
            del detector
            self._free_gpu()
        except Exception as exc:
            logger.warning(f"Detection failed: {exc}")

        # ── Stage 1b: Zero-Shot Fallback (OWL-ViT) ───────────────────────────
        if not detections:
            try:
                from nutrisnap.pipeline.zero_shot import ZeroShotFoodDetector
                
                # List of common dishes we want to catch if YOLO fails
                queries = [
                    "pizza", "burger", "salad", "biryani", "steak", "pasta", 
                    "sandwich", "soup", "plate of food", "bowl of food", 
                    "fruit", "vegetable", "bread", "dessert", "drink",
                    "dal", "paneer", "roti", "naan", "idli", "dosa", "samosa",
                    "rice", "noodle", "chicken", "fish", "egg", "curry",
                    "taco", "burrito", "sushi", "pancake", "waffle", "yogurt"
                ]
                
                zs_detector = ZeroShotFoodDetector(device=self.device)
                # Tiled inference is enabled by default in our update
                detections = zs_detector.detect(image_path, queries)
                zero_shot_labels = [d.get("label") for d in detections]
                logger.info(f"Zero-Shot fallback detected {len(detections)} items: {zero_shot_labels}")
                
                zs_detector.unload()
                del zs_detector
                self._free_gpu()
            except Exception as exc:
                logger.warning(f"Zero-Shot fallback failed: {exc}")

        # ── Stage 1c: Edamam Fallback (Last Resort) ──────────────────────────
        if not detections:
            try:
                # In production, this would call Edamam's image recognition API
                # For the demo/batch test, we log the attempt.
                logger.info("All local detectors failed. Attempting Edamam/External fallback...")
                # implementation = EdamamClient().detect(image_path)
            except Exception as exc:
                logger.error(f"External fallback failed: {exc}")

        # Handle no food detected case
        if not detections:
            logger.info("No food detected in pipeline")
            return PipelineResult(
                total_mass_g=0,
                validation_summary={
                    "is_valid": False,
                    "reasoning": "No food detected",
                    "corrections": []
                },
                latency_seconds=time.perf_counter() - t0
            )

        # ── Stage 2: Segmentation (SAM 2) ─────────────────────────────────────
        masks: list[Any] = []
        try:
            from nutrisnap.pipeline.segmenter import FoodSegmenterSAM2

            segmenter = FoodSegmenterSAM2(device=self.device)
            import numpy as np
            from PIL import Image

            img = np.array(Image.open(image_path).convert("RGB"))
            for det in detections:
                box = det.get("bbox_xyxy")
                if box is not None:
                    # Potential optimization: crop if item is small
                    result = segmenter.segment_with_box(img, box)
                    masks.append(result.get("combined_mask"))
                else:
                    masks.append(None)
            if hasattr(segmenter, "unload"):
                segmenter.unload()
            del segmenter
            self._free_gpu()
        except Exception as exc:
            logger.warning(f"Segmentation failed: {exc}")
            masks = [None] * len(detections)

        # ── Stage 3: Depth estimation (GLPN) ─────────────────────────────────
        depth_map = None
        try:
            from nutrisnap.pipeline.depth import DepthEstimatorGLPN

            depth_est = DepthEstimatorGLPN(device=self.device)
            depth_map = depth_est.estimate(image_path)
            if hasattr(depth_est, "unload"):
                depth_est.unload()
            del depth_est
            self._free_gpu()
        except Exception as exc:
            logger.warning(f"Depth estimation failed: {exc}")

        # ── Stage 4: Mass / Nutrition (MultiFoodMerger) ───────────────────────
        merged = None
        try:
            if depth_map is not None:
                from nutrisnap.pipeline.merger import MultiFoodMerger

                merger = MultiFoodMerger()
                valid_masks = [m for m in masks if m is not None]
                valid_dets = [d for d, m in zip(detections, masks) if m is not None]
                if valid_dets:
                    merged = merger.merge(valid_dets, valid_masks, depth_map)
                del merger
                self._free_gpu()
        except Exception as exc:
            logger.warning(f"Merging failed: {exc}")

        # Build items list
        items: list[dict] = []
        if merged is not None:
            for food_item in merged.items:
                items.append(
                    {
                        "label": food_item.label,
                        "confidence": food_item.confidence,
                        "volume_cm3": food_item.volume_cm3,
                        "mass_g": food_item.mass_g,
                        "calories": food_item.total_calories,
                        "protein": food_item.total_protein,
                        "carbs": food_item.total_carbs,
                        "fat": food_item.total_fat,
                        "fiber": food_item.total_fiber,
                        "saturated_fat": food_item.total_saturated_fat,
                        "sugars": food_item.total_sugars,
                    }
                )

        total_cal = sum(i["calories"] for i in items)
        total_mass = sum(i["mass_g"] for i in items)
        total_prot = sum(i["protein"] for i in items)
        total_carbs = sum(i["carbs"] for i in items)
        total_fat = sum(i["fat"] for i in items)
        total_fiber = sum(i["fiber"] for i in items)
        total_sat_fat = sum(i["saturated_fat"] for i in items)
        total_sugars = sum(i["sugars"] for i in items)

        # ── Stage 5: Gemini Validation ────────────────────────────────────────
        validation: dict = {
            "is_valid": True,
            "reasoning": "No validation",
            "corrections": [],
        }
        try:
            import asyncio

            from nutrisnap.verification.llm_validator import LLMValidator

            validator = LLMValidator()
            validation_result = asyncio.run(
                validator.validate_meal(items, total_cal, image_path)
            )
            validation = {
                "is_valid": validation_result.is_valid,
                "reasoning": validation_result.reasoning,
                "corrections": validation_result.corrections,
            }
        except Exception as exc:
            logger.warning(f"LLM validation failed: {exc}")

        # ── Stage 6: Health Scoring ──────────────────────────────────────────
        health_score = {"grade": "C", "summary": "Balance not analyzed"}
        try:
            from nutrisnap.verification.health_scorer import HealthScorer
            
            nutrition_summary = {
                "calories": total_cal,
                "protein": total_prot,
                "carbs": total_carbs,
                "fat": total_fat,
                "fiber": total_fiber,
                "saturated_fat": total_sat_fat,
                "sugars": total_sugars,
            }
            health_score = HealthScorer.calculate_score(nutrition_summary)
            validation["health_score"] = health_score
        except Exception as exc:
            logger.warning(f"Health scoring failed: {exc}")

        latency = time.perf_counter() - t0
        logger.info(
            f"Pipeline complete in {latency:.2f}s — {len(items)} items, {total_cal:.0f} kcal"
        )

        return PipelineResult(
            items=items,
            total_calories=total_cal,
            total_mass_g=total_mass,
            total_protein=total_prot,
            total_carbs=total_carbs,
            total_fat=total_fat,
            total_fiber=total_fiber,
            total_saturated_fat=total_sat_fat,
            total_sugars=total_sugars,
            validation_summary=validation,
            latency_seconds=latency,
            item_count=len(items),
        )

    def teardown(self) -> None:
        self._free_gpu()
        logger.info("RealOrchestrator torn down")


# ─────────────────────────────────────────────────────────────────────────────
# Public facade
# ─────────────────────────────────────────────────────────────────────────────


class SequentialOrchestrator:
    """
    Public facade that delegates to mock or real orchestrator.

    Usage::
        # In lifespan
        app.state.orchestrator = SequentialOrchestrator(device="cuda")

        # In route handler
        result = await run_in_executor(None, app.state.orchestrator.predict, path)
    """

    def __init__(self, device: str = "cuda", mock: bool = False) -> None:
        if mock:
            self._impl: _MockOrchestrator | _RealOrchestrator = _MockOrchestrator()
            logger.info("SequentialOrchestrator using mock backend")
        else:
            self._impl = _RealOrchestrator(device=device)

    def predict(self, image_path: str) -> PipelineResult:
        """Run the full pipeline. Blocking — run in a thread pool from async context."""
        return self._impl.predict(image_path)

    def teardown(self) -> None:
        self._impl.teardown()
