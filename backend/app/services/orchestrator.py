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
            "validation_summary": self.validation_summary,
            "latency_seconds": self.latency_seconds,
            "item_count": self.item_count,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Mock (CI / no-GPU) implementation
# ─────────────────────────────────────────────────────────────────────────────


class _MockOrchestrator:
    """Returns plausible-looking mock results without touching the GPU."""

    def predict(self, image_path: str) -> PipelineResult:
        logger.debug(f"MockOrchestrator.predict({image_path})")
        return PipelineResult(
            items=[
                {
                    "label": "biryani",
                    "confidence": 0.91,
                    "volume_cm3": 420.0,
                    "mass_g": 350.0,
                    "calories": 450.0,
                    "protein": 18.0,
                    "carbs": 62.0,
                    "fat": 12.0,
                }
            ],
            total_calories=450.0,
            total_mass_g=350.0,
            total_protein=18.0,
            total_carbs=62.0,
            total_fat=12.0,
            validation_summary={
                "is_valid": True,
                "reasoning": "Mock OK",
                "corrections": [],
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

        # ── Stage 1: Detection (YOLOv8) ──────────────────────────────────────
        detections: list[dict] = []
        try:
            from nutrisnap.pipeline.multi_food import MultiFoodDetector

            detector = MultiFoodDetector(device=self.device)
            detections = detector.detect(image_path)
            logger.info(f"Detected {len(detections)} items")
            if hasattr(detector, "unload"):
                detector.unload()
            del detector
            self._free_gpu()
        except Exception as exc:
            logger.warning(f"Detection failed: {exc}")

        if not detections:
            return PipelineResult(latency_seconds=time.perf_counter() - t0)

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
                import numpy as np

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
                    }
                )

        total_cal = sum(i["calories"] for i in items)
        total_mass = sum(i["mass_g"] for i in items)

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

        latency = time.perf_counter() - t0
        logger.info(
            f"Pipeline complete in {latency:.2f}s — {len(items)} items, {total_cal:.0f} kcal"
        )

        return PipelineResult(
            items=items,
            total_calories=total_cal,
            total_mass_g=total_mass,
            total_protein=sum(i["protein"] for i in items),
            total_carbs=sum(i["carbs"] for i in items),
            total_fat=sum(i["fat"] for i in items),
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
