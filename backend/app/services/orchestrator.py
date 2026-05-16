"""SequentialOrchestrator: Load-Run-Unload pipeline for VRAM-constrained environments.

Manages the full multi-food inference pipeline on a single 4GB GPU by
running each stage sequentially and releasing GPU memory between stages.
"""

from __future__ import annotations

import gc
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger


def _iou(box1: list[int], box2: list[int]) -> float:
    """Calculate Intersection over Union for two [x1,y1,x2,y2] boxes."""
    x1, y1, x2, y2 = box1
    x3, y3, x4, y4 = box2
    ix1, iy1 = max(x1, x3), max(y1, y3)
    ix2, iy2 = min(x2, x4), min(y2, y4)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area1 = (x2 - x1) * (y2 - y1)
    area2 = (x4 - x3) * (y4 - y3)
    union = area1 + area2 - inter
    return inter / union if union > 0 else 0.0


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
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

    def _refine_with_gemini(self, image_path: str, detections: list[dict]) -> list[dict]:
        """Use Gemini to refine/correct detection labels (Stage 1c)."""
        import asyncio
        from nutrisnap.verification.llm_validator import LLMValidator
        
        validator = LLMValidator()
        if not validator.is_available:
            return detections

        labels = [d["label"] for d in detections]
        prompt = f"""Identify the food items in this image.
        
        A computer vision model detected these raw labels: {labels}.
        
        Rules:
        1. CONSOLIDATE DISHES: If multiple detections are components of a single dish (e.g., rice, chicken pieces, and spices in a Biryani), label them with the EXACT SAME dish name (e.g., "Chicken Biryani").
        2. BE SPECIFIC: Use specific names for Indian cuisine (e.g., "Raita", "Pickled Onions", "Dal Makhani", "Paneer Tikka").
        3. ORDER MATTERS: Return exactly {len(labels)} labels in the same order as the input list.
        4. JSON ONLY: Return ONLY a JSON list of strings. No explanations.
        """
        
        try:
            # We reuse the multimodal validator logic
            logger.info("Stage 1c: Requesting Gemini refinement for labels...")
            result = asyncio.run(validator.call_llm(prompt, image_path))
            
            # The validator parses JSON. We expect a list or a dict containing a list.
            if isinstance(result, list):
                corrected_labels = result
            elif isinstance(result, dict) and "corrections" in result:
                corrected_labels = [c.get("new_label", c.get("label")) for c in result["corrections"]]
            elif isinstance(result, dict) and "labels" in result:
                corrected_labels = result["labels"]
            elif isinstance(result, dict) and any(isinstance(v, list) for v in result.values()):
                # Fallback: find the first list in the dict
                corrected_labels = next(v for v in result.values() if isinstance(v, list))
            else:
                logger.warning(f"Stage 1c: Unexpected Gemini refinement format: {result}")
                return detections

            # Apply corrections
            for i, label in enumerate(corrected_labels):
                if i < len(detections):
                    if detections[i]["label"] != label:
                        logger.info(f"Stage 1c: Correcting '{detections[i]['label']}' -> '{label}'")
                        detections[i]["label"] = label
            
            return detections
        except Exception as e:
            logger.error(f"Stage 1c: Gemini refinement failed: {e}")
            return detections



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

        # ── Stage 1: Detection — OWL-ViT Primary → YOLO Supplement ─────────────
        #
        # OWL-ViT runs first with a comprehensive food query list and a low
        # confidence threshold (0.05).  This works on any image — even heavily
        # compressed ones — because it uses text semantics rather than fixed
        # class IDs.  YOLO then runs as a secondary pass to catch any additional
        # items it is confident about, and those are merged in.
        #
        # Rationale: generic YOLOv8n is trained on COCO-80 classes (many of
        # which are not food at all) and performs poorly on Indian dishes and
        # ultra-compressed images.  OWL-ViT zero-shot is our reliable lifeline.
        # ─────────────────────────────────────────────────────────────────────
        FOOD_QUERIES = [
            # Indian dishes - more descriptive for OWL-ViT
            "biryani plate", "chicken biryani rice", "rice with meat", 
            "indian curry bowl", "naan bread", "roti bread",
            "paneer curry", "lentil dal", "samosa snack", "dosa wrap", 
            "idli cakes", "chole bhature plate",
            # International dishes
            "pizza", "burger", "sandwich", "vegetable salad", "pasta dish", 
            "grilled steak", "sushi rolls", "soup bowl", "fried rice",
            # Generic food categories (catch-all)
            "plate of food", "bowl of food", "meal", "food item",
            "fruit", "vegetables", "bread", "dessert", "cake",
            "rice dish", "curry dish", "mixed dish",
        ]

        detections: list[dict] = []

        # ── Stage 1a: OWL-ViT (Primary) ──────────────────────────────────────
        try:
            from nutrisnap.pipeline.zero_shot import ZeroShotFoodDetector

            zs_detector = ZeroShotFoodDetector(
                device=self.device,
                confidence_threshold=0.05,   # low threshold — more recall
            )
            detections = zs_detector.detect(image_path, FOOD_QUERIES, tiled=True)
            zero_shot_labels = [f"{d.get('label')} ({d.get('confidence', 0):.2f})" for d in detections]
            logger.info(
                f"OWL-ViT (primary) detected {len(detections)} items: {zero_shot_labels}"
            )
            zs_detector.unload()
            del zs_detector
            self._free_gpu()
        except Exception as exc:
            logger.warning(f"OWL-ViT primary detection failed: {exc}")

        # ── Stage 1b: YOLOv8 (Secondary supplement) ──────────────────────────
        try:
            from nutrisnap.pipeline.multi_food import MultiFoodDetector, LIKELY_FOOD_CLASSES
            import cv2
            import numpy as np

            img_test = cv2.imread(image_path)
            if img_test is not None and np.mean(img_test) < 1.0:
                logger.warning("Image appears black or extremely dark — YOLO may fail.")

            # Resolve model path relative to backend root, falling back to
            # Ultralytics auto-download (yolov8n.pt downloads to its own cache)
            _backend_root = Path(__file__).parents[2]
            _specialized = _backend_root / "models" / "food_specialized_yolov8.pt"
            model_to_use = str(_specialized) if _specialized.exists() else "yolov8n.pt"

            detector = MultiFoodDetector(model_name=model_to_use, device=self.device)
            raw_detections = detector.detect(image_path, imgsz=1280)

            yolo_food = [
                d for d in raw_detections
                if d.get("class_id") in LIKELY_FOOD_CLASSES and d.get("confidence", 0) > 0.5
            ]
            logger.info(
                f"YOLOv8 ({model_to_use}) found {len(yolo_food)} high-confidence food items"
            )

            # Merge YOLO hits that don't significantly overlap existing OWL-ViT detections
            for yd in yolo_food:
                overlap = any(
                    _iou(yd["bbox_xyxy"], od["bbox_xyxy"]) > 0.4
                    for od in detections
                    if od.get("bbox_xyxy")
                )
                if not overlap:
                    detections.append(yd)

            if hasattr(detector, "unload"):
                detector.unload()
            del detector
            self._free_gpu()
        except Exception as exc:
            logger.warning(f"YOLOv8 secondary pass failed (non-fatal): {exc}")

        # ── Stage 1c: Gemini Refinement (Skipped to save quota) ──────────────
        # Combined with Stage 5 validation for efficiency.
        pass

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

            img = Image.open(image_path).convert("RGB")
        
            # Downscale large images to prevent CUDA OOM on 4GB GPUs
            MAX_INFERENCE_DIM = 1024
            if img.width > MAX_INFERENCE_DIM or img.height > MAX_INFERENCE_DIM:
                img.thumbnail((MAX_INFERENCE_DIM, MAX_INFERENCE_DIM), Image.Resampling.LANCZOS)
                logger.info(f"Resized image for inference to {img.width}x{img.height}")
            
            img_arr = np.array(img)
            for det in detections:
                box = det.get("bbox_xyxy")
                if box is not None:
                    # Potential optimization: crop if item is small
                    result = segmenter.segment_with_box(img_arr, box)
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
                        "confidence": float(food_item.confidence),
                        "volume_cm3": float(food_item.volume_cm3),
                        "mass_g": float(food_item.mass_g),
                        "calories": float(food_item.total_calories),
                        "protein": float(food_item.total_protein),
                        "carbs": float(food_item.total_carbs),
                        "fat": float(food_item.total_fat),
                        "fiber": float(food_item.total_fiber),
                        "saturated_fat": float(food_item.total_saturated_fat),
                        "sugars": float(food_item.total_sugars),
                    }
                )

        total_cal = float(sum(i["calories"] for i in items))
        total_mass = float(sum(i["mass_g"] for i in items))
        total_prot = float(sum(i["protein"] for i in items))
        total_carbs = float(sum(i["carbs"] for i in items))
        total_fat = float(sum(i["fat"] for i in items))
        total_fiber = float(sum(i["fiber"] for i in items))
        total_sat_fat = float(sum(i["saturated_fat"] for i in items))
        total_sugars = float(sum(i["sugars"] for i in items))

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

            if validation_result.final_items:
                items = validation_result.final_items
                total_cal = float(sum(i.get("calories", 0) for i in items))
                total_mass = float(sum(i.get("mass_g", 0) for i in items))
                total_prot = float(sum(i.get("protein", 0) for i in items))
                total_carbs = float(sum(i.get("carbs", 0) for i in items))
                total_fat = float(sum(i.get("fat", 0) for i in items))
                total_fiber = float(sum(i.get("fiber", 0) for i in items))
                total_sat_fat = float(sum(i.get("saturated_fat", 0) for i in items))
                total_sugars = float(sum(i.get("sugars", 0) for i in items))
                validation["final_items"] = items
                validation["authority"] = "api_key"
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
