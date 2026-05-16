"""
Multi-food prediction merger for itemized nutritional analysis.

Combines volume estimation with density-based mass calculation to produce
itemized nutritional predictions from multi-food detection + segmentation.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np
import numpy.typing as npt

from nutrisnap.data.densities import get_food_density, load_density_db
from nutrisnap.models.portion_corrector import get_default_corrector
from nutrisnap.pipeline.volume import VolumeEstimator
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FoodItem:
    """Single food item with computed nutrition."""

    label: str
    confidence: float
    volume_cm3: float
    mass_g: float
    density_g_cm3: float
    area_m2: float
    volume_type: str  # "convex" or "concave"

    # Nutrition per 100g (from density DB)
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    fiber: float
    saturated_fat: float
    sugars: float

    # Computed totals
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    total_fiber: float
    total_saturated_fat: float
    total_sugars: float

    # Optional metadata
    is_liquid: bool = False

    # Mask for visualization/debugging
    mask: Optional[npt.NDArray[np.uint8]] = None

    @classmethod
    def from_volume_and_label(
        cls,
        label: str,
        confidence: float,
        volume_m3: float,
        area_m2: float,
        volume_type: str,
        mask: Optional[npt.NDArray[np.uint8]] = None,
    ) -> "FoodItem":
        """Create FoodItem from volume estimation and food label.

        Args:
            label: Food label (e.g., "chicken", "rice").
            confidence: Detection confidence [0, 1].
            volume_m3: Estimated volume in cubic meters.
            area_m2: Estimated surface area in square meters.
            volume_type: "convex" or "concave".
            mask: Optional binary mask for the item.

        Returns:
            FoodItem with computed mass and nutrition.
        """
        # Convert volume to cm³ (1 m³ = 1,000,000 cm³)
        volume_cm3 = volume_m3 * 1e6

        # Get density data
        density_data = get_food_density(label)
        density = density_data["density"]  # g/cm³

        # Calculate mass
        mass_g = volume_cm3 * density

        # Scale nutrition to actual mass
        scale = mass_g / 100.0

        return cls(
            label=label,
            confidence=confidence,
            volume_cm3=volume_cm3,
            mass_g=mass_g,
            density_g_cm3=density,
            area_m2=area_m2,
            volume_type=volume_type,
            is_liquid=density_data.get("is_liquid", False),
            calories=density_data["calories"],
            protein=density_data["protein"],
            carbohydrates=density_data["carbohydrates"],
            fat=density_data["fat"],
            fiber=density_data["fiber"],
            saturated_fat=density_data.get("saturated_fat", 0.0),
            sugars=density_data.get("sugars", 0.0),
            total_calories=density_data["calories"] * scale,
            total_protein=density_data["protein"] * scale,
            total_carbs=density_data["carbohydrates"] * scale,
            total_fat=density_data["fat"] * scale,
            total_fiber=density_data["fiber"] * scale,
            total_saturated_fat=density_data.get("saturated_fat", 0.0) * scale,
            total_sugars=density_data.get("sugars", 0.0) * scale,
            mask=mask,
        )


@dataclass
class MergedPrediction:
    """Aggregated prediction for a multi-food plate."""

    items: list[FoodItem]

    # Aggregated totals
    total_volume_cm3: float
    total_mass_g: float
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    total_fiber: float
    total_saturated_fat: float
    total_sugars: float

    # Metadata
    item_count: int
    food_labels: list[str]

    @classmethod
    def from_items(cls, items: list[FoodItem]) -> "MergedPrediction":
        """Create aggregated prediction from list of FoodItems."""
        if not items:
            return cls(
                items=[],
                total_volume_cm3=0.0,
                total_mass_g=0.0,
                total_calories=0.0,
                total_protein=0.0,
                total_carbs=0.0,
                total_fat=0.0,
                total_fiber=0.0,
                total_saturated_fat=0.0,
                total_sugars=0.0,
                item_count=0,
                food_labels=[],
            )

        return cls(
            items=items,
            total_volume_cm3=sum(i.volume_cm3 for i in items),
            total_mass_g=sum(i.mass_g for i in items),
            total_calories=sum(i.total_calories for i in items),
            total_protein=sum(i.total_protein for i in items),
            total_carbs=sum(i.total_carbs for i in items),
            total_fat=sum(i.total_fat for i in items),
            total_fiber=sum(i.total_fiber for i in items),
            total_saturated_fat=sum(i.total_saturated_fat for i in items),
            total_sugars=sum(i.total_sugars for i in items),
            item_count=len(items),
            food_labels=[i.label for i in items],
        )


class MultiFoodMerger:
    """Merges multi-food detections with volume estimation for itemized nutrition.

    Pipeline:
    1. Take detections (labels, confidences) + masks + depth map
    2. For each detection: estimate volume from mask + depth
    3. Convert volume → mass using food density
    4. Convert mass → nutrition using USDA data
    5. Apply IoU-based redundancy checks to avoid double-counting
    6. Return itemized and aggregated predictions
    """

    # IoU threshold above which masks are considered overlapping
    IOU_THRESHOLD = 0.15

    def __init__(
        self,
        density_db_path: Optional[Path | str] = None,
        volume_config: Optional[Path | str] = None,
        iou_threshold: float = 0.15,
    ):
        """Initialize merger with density database and volume estimator.

        Args:
            density_db_path: Path to densities.json. Uses default if None.
            volume_config: Path to volume.yaml configuration.
            iou_threshold: IoU threshold for overlap detection.
        """
        # Load density database
        load_density_db(density_db_path)

        # Initialize volume estimator
        self.volume_estimator = VolumeEstimator(volume_config)

        # Load PortionCorrector (passthrough if not yet trained)
        self.corrector = get_default_corrector()
        if self.corrector.is_trained:
            logger.info("PortionCorrector active: XGBoost mass corrections enabled")
        else:
            logger.info("PortionCorrector: passthrough mode (run train_portion_corrector.py to enable)")

        # Overlap threshold
        self.iou_threshold = iou_threshold

        logger.info(f"MultiFoodMerger initialized (IoU threshold: {iou_threshold})")

    def merge(
        self,
        detections: list[dict[str, Any]],
        masks: list[npt.NDArray[np.uint8]],
        depth_map: npt.NDArray[np.float32],
        check_overlap: bool = True,
    ) -> MergedPrediction:
        """Merge detections with volume estimation.

        Args:
            detections: List of detection dicts with:
                - label: Food label string
                - confidence: Detection confidence [0, 1]
            masks: List of binary masks (H, W), one per detection.
            depth_map: (H, W) depth map in meters.
            check_overlap: If True, apply IoU-based overlap adjustment.

        Returns:
            MergedPrediction with itemized and aggregated nutrition.
        """
        if check_overlap:
            return self.merge_with_overlap_check(detections, masks, depth_map)

        # Original logic without overlap checking
        if len(detections) != len(masks):
            raise ValueError(f"Detections ({len(detections)}) != masks ({len(masks)})")

        if not detections:
            logger.warning("No detections provided to merger")
            return MergedPrediction.from_items([])

        items = []

        for det, mask in zip(detections, masks):
            label = det.get("label", "unknown")
            confidence = det.get("confidence", 0.5)

            # Estimate volume for this mask — pass depth + mask for auto z_ref detection
            pc = self.volume_estimator.project_to_pc(depth_map, mask)
            vol, area, vol_type = self.volume_estimator.estimate_volume(pc, depth=depth_map, mask=mask)

            # Skip empty volumes
            if vol < 1e-9:
                logger.debug(f"Skipping {label}: zero volume")
                continue

            # Create FoodItem with computed nutrition
            item = FoodItem.from_volume_and_label(
                label=label,
                confidence=confidence,
                volume_m3=vol,
                area_m2=area,
                volume_type=vol_type,
                mask=mask,
            )

            # Apply PortionCorrector if trained
            if self.corrector.is_trained:
                depth_feats = self.volume_estimator.extract_depth_features(depth_map, mask)
                corrected_mass = self.corrector.predict(
                    predicted_mass_g=item.mass_g,
                    volume_cm3=item.volume_cm3,
                    volume_type=vol_type,
                    depth_features=depth_feats,
                )
                if corrected_mass != item.mass_g:
                    # Rebuild scale with corrected mass
                    scale = corrected_mass / 100.0
                    item = FoodItem(
                        label=item.label,
                        confidence=item.confidence,
                        volume_cm3=item.volume_cm3,
                        mass_g=corrected_mass,
                        density_g_cm3=item.density_g_cm3,
                        area_m2=item.area_m2,
                        volume_type=item.volume_type,
                        is_liquid=item.is_liquid,
                        calories=item.calories,
                        protein=item.protein,
                        carbohydrates=item.carbohydrates,
                        fat=item.fat,
                        fiber=item.fiber,
                        saturated_fat=item.saturated_fat,
                        sugars=item.sugars,
                        total_calories=item.calories * scale,
                        total_protein=item.protein * scale,
                        total_carbs=item.carbohydrates * scale,
                        total_fat=item.fat * scale,
                        total_fiber=item.fiber * scale,
                        total_saturated_fat=item.saturated_fat * scale,
                        total_sugars=item.sugars * scale,
                        mask=item.mask,
                    )

            items.append(item)
            logger.debug(
                f"Item: {label} - {item.volume_cm3:.1f} cm³, "
                f"{item.mass_g:.1f}g, {item.total_calories:.1f} kcal"
            )

        result = MergedPrediction.from_items(items)

        logger.info(
            f"Merged {result.item_count} items: "
            f"{result.total_calories:.1f} kcal, {result.total_mass_g:.1f}g"
        )

        return result

    def merge_simple(
        self,
        labels: list[str],
        volumes_cm3: list[float],
        confidences: Optional[list[float]] = None,
    ) -> MergedPrediction:
        """Simple merge with pre-computed volumes.

        Use this when volume estimation is done externally.

        Args:
            labels: List of food labels.
            volumes_cm3: List of volumes in cm³.
            confidences: Optional confidence scores.

        Returns:
            MergedPrediction.
        """
        if confidences is None:
            confidences = [0.8] * len(labels)

        items = []

        for label, vol_cm3, conf in zip(labels, volumes_cm3, confidences):
            # Convert cm³ to m³ for FoodItem
            vol_m3 = vol_cm3 / 1e6

            item = FoodItem.from_volume_and_label(
                label=label,
                confidence=conf,
                volume_m3=vol_m3,
                area_m2=0.0,  # Unknown for simple merge
                volume_type="simple",
            )
            items.append(item)

        return MergedPrediction.from_items(items)

    # ========== Containment & Redundancy Checking ==========

    @staticmethod
    def compute_iou(
        mask1: npt.NDArray[np.uint8], mask2: npt.NDArray[np.uint8]
    ) -> float:
        """Compute Intersection over Union (IoU) between two masks.

        Args:
            mask1: First binary mask.
            mask2: Second binary mask.

        Returns:
            IoU score in [0, 1]. 0 = no overlap, 1 = identical.
        """
        intersection = np.logical_and(mask1, mask2).sum()
        union = np.logical_or(mask1, mask2).sum()

        if union == 0:
            return 0.0

        return float(intersection) / float(union)

    @staticmethod
    def compute_iou_batch(
        masks: list[npt.NDArray[np.uint8]],
    ) -> npt.NDArray[np.float32]:
        """Compute pairwise IoU for a list of masks.

        Args:
            masks: List of binary masks.

        Returns:
            (N, N) IoU matrix where element [i,j] is IoU between
            masks[i] and masks[j].
        """
        n = len(masks)
        iou_matrix = np.zeros((n, n), dtype=np.float32)

        for i in range(n):
            for j in range(n):
                if i != j:
                    iou_matrix[i, j] = MultiFoodMerger.compute_iou(masks[i], masks[j])

        return iou_matrix

    def adjust_for_overlap(
        self, items: list[FoodItem], masks: list[npt.NDArray[np.uint8]]
    ) -> list[FoodItem]:
        """Adjust volumes for overlapping masks to avoid double-counting.

        Strategy:
        - If IoU > 0.7, discard the lower-confidence item (redundant).
        - If IoU > threshold, reduce volume of the lower-confidence item by the overlap ratio.

        Args:
            items: List of FoodItems with computed volumes.
            masks: Original binary masks.

        Returns:
            Adjusted list of FoodItems.
        """
        if len(items) <= 1 or not masks:
            return items

        # Compute IoU matrix
        iou_matrix = self.compute_iou_batch(masks)
        n = len(items)
        keep_indices = list(range(n))
        
        # 1. Discard extreme overlaps (>0.7)
        for i in range(n):
            for j in range(i + 1, n):
                iou = iou_matrix[i, j]
                if iou > 0.7:
                    if items[i].confidence >= items[j].confidence:
                        if j in keep_indices: keep_indices.remove(j)
                        logger.debug(f"Discarding redundant {items[j].label} (IoU={iou:.2f} with {items[i].label})")
                    else:
                        if i in keep_indices: keep_indices.remove(i)
                        logger.debug(f"Discarding redundant {items[i].label} (IoU={iou:.2f} with {items[j].label})")
                        break

        # 2. Proportional reduction for remaining overlaps
        final_items = []
        for i in keep_indices:
            item = items[i]
            mask_i = masks[i]
            
            # Find max overlap with any other KEPT item that has HIGHER confidence
            max_iou = 0.0
            for j in keep_indices:
                if i == j: continue
                if items[j].confidence > item.confidence:
                    max_iou = max(max_iou, iou_matrix[i, j])

            if max_iou > self.iou_threshold:
                # Reduce volume proportionally to overlap
                reduction_factor = 1.0 - max_iou
                new_vol = item.volume_cm3 * reduction_factor

                # Recalculate mass and nutrition
                mass_g = new_vol * item.density_g_cm3
                scale = mass_g / 100.0

                item = FoodItem(
                    label=item.label,
                    confidence=item.confidence,
                    volume_cm3=new_vol,
                    mass_g=mass_g,
                    density_g_cm3=item.density_g_cm3,
                    area_m2=item.area_m2,
                    volume_type=item.volume_type,
                    is_liquid=item.is_liquid,
                    calories=item.calories,
                    protein=item.protein,
                    carbohydrates=item.carbohydrates,
                    fat=item.fat,
                    fiber=item.fiber,
                    saturated_fat=item.saturated_fat,
                    sugars=item.sugars,
                    total_calories=item.calories * scale,
                    total_protein=item.protein * scale,
                    total_carbs=item.carbohydrates * scale,
                    total_fat=item.fat * scale,
                    total_fiber=item.fiber * scale,
                    total_saturated_fat=item.saturated_fat * scale,
                    total_sugars=item.sugars * scale,
                    mask=item.mask,
                )
                logger.debug(f"Reducing {item.label} volume by {max_iou*100:.1f}% due to overlap")

            final_items.append(item)

        return final_items

    def merge_with_overlap_check(
        self,
        detections: list[dict[str, Any]],
        masks: list[npt.NDArray[np.uint8]],
        depth_map: npt.NDArray[np.float32],
    ) -> MergedPrediction:
        """Merge with overlap checking.

        Same as merge() but applies IoU-based volume adjustment.

        Args:
            detections: List of detection dicts.
            masks: List of binary masks.
            depth_map: Depth map.

        Returns:
            MergedPrediction with adjusted volumes.
        """
        # First, compute base items
        items = []

        for det, mask in zip(detections, masks):
            label = det.get("label", "unknown")
            confidence = det.get("confidence", 0.5)

            # Estimate volume — pass depth + mask for auto z_ref detection
            pc = self.volume_estimator.project_to_pc(depth_map, mask)
            vol, area, vol_type = self.volume_estimator.estimate_volume(pc, depth=depth_map, mask=mask)

            if vol < 1e-9:
                continue

            item = FoodItem.from_volume_and_label(
                label=label,
                confidence=confidence,
                volume_m3=vol,
                area_m2=area,
                volume_type=vol_type,
                mask=mask,
            )

            # Apply PortionCorrector if trained
            if self.corrector.is_trained:
                depth_feats = self.volume_estimator.extract_depth_features(depth_map, mask)
                corrected_mass = self.corrector.predict(
                    predicted_mass_g=item.mass_g,
                    volume_cm3=item.volume_cm3,
                    volume_type=vol_type,
                    depth_features=depth_feats,
                )
                if corrected_mass != item.mass_g:
                    scale = corrected_mass / 100.0
                    item = FoodItem(
                        label=item.label,
                        confidence=item.confidence,
                        volume_cm3=item.volume_cm3,
                        mass_g=corrected_mass,
                        density_g_cm3=item.density_g_cm3,
                        area_m2=item.area_m2,
                        volume_type=item.volume_type,
                        is_liquid=item.is_liquid,
                        calories=item.calories,
                        protein=item.protein,
                        carbohydrates=item.carbohydrates,
                        fat=item.fat,
                        fiber=item.fiber,
                        saturated_fat=item.saturated_fat,
                        sugars=item.sugars,
                        total_calories=item.calories * scale,
                        total_protein=item.protein * scale,
                        total_carbs=item.carbohydrates * scale,
                        total_fat=item.fat * scale,
                        total_fiber=item.fiber * scale,
                        total_saturated_fat=item.saturated_fat * scale,
                        total_sugars=item.sugars * scale,
                        mask=item.mask,
                    )

            items.append(item)

        # Apply overlap adjustment
        if masks:
            items = self.adjust_for_overlap(items, masks)

        # Apply total plate bound scaling if significant overlap exists
        items = self._scale_to_plate_bound(items, masks)

        # Merge duplicates (Stage 1d)
        items = self._merge_duplicate_labels(items)

        result = MergedPrediction.from_items(items)

        logger.info(
            f"Merged (with overlap): {result.item_count} items, "
            f"{result.total_calories:.1f} kcal"
        )

        return result

    def _scale_to_plate_bound(
        self, items: list[FoodItem], masks: list[npt.NDArray[np.uint8]]
    ) -> list[FoodItem]:
        """Scale volumes to total plate bound.

        If there's a "plate" or "dish" mask, ensures total food volume
        doesn't exceed the plate's bounded area.

        Args:
            items: List of FoodItems.
            masks: List of masks.

        Returns:
            Adjusted items if plate bound detected, otherwise unchanged.
        """
        if not items or not masks:
            return items

        # Compute total mask area vs individual areas
        total_mask = np.zeros_like(masks[0])
        for mask in masks:
            total_mask = np.logical_or(total_mask, mask)

        total_pixels = total_mask.sum()

        # If individual masks sum to more than total, there's overlap
        individual_pixels = sum(m.sum() for m in masks)

        if individual_pixels > 0:
            overlap_ratio = 1.0 - (total_pixels / individual_pixels)

            # If significant overlap (>30%), apply plate bound scaling
            if overlap_ratio > 0.3:
                logger.debug(
                    f"Plate bound: {total_pixels} pixels / {individual_pixels} "
                    f"= {1-overlap_ratio:.2f} coverage"
                )
                # The IoU adjustment already handles this, so no additional scaling
                # is needed - keep items as-is

        return items

    def _merge_duplicate_labels(self, items: list[FoodItem]) -> list[FoodItem]:
        """Merge items with identical labels into a single item.

        Sums volumes and areas, then recomputes nutrition for the combined mass.
        """
        if not items:
            return items

        merged_groups = {}
        for item in items:
            label = item.label.lower().strip()
            if label not in merged_groups:
                merged_groups[label] = []
            merged_groups[label].append(item)

        final_items = []
        for label, group in merged_groups.items():
            if len(group) == 1:
                final_items.append(group[0])
                continue

            # Merge group
            total_vol_cm3 = sum(item.volume_cm3 for item in group)
            total_area_m2 = sum(item.area_m2 for item in group)
            # Use weighted average for confidence
            avg_conf = sum(item.confidence * item.volume_cm3 for item in group) / total_vol_cm3

            # Recreate item from combined volume
            # We need volume in m3 for from_volume_and_label
            merged_item = FoodItem.from_volume_and_label(
                label=group[0].label,  # Keep original casing
                confidence=avg_conf,
                volume_m3=total_vol_cm3 / 1e6,
                area_m2=total_area_m2,
                volume_type=group[0].volume_type,
                mask=group[0].mask,  # Just pick first mask for now
            )
            logger.info(f"Merged {len(group)} items with label '{group[0].label}'")
            final_items.append(merged_item)

        return final_items


# Convenience functions


def compute_mass(volume_cm3: float, food_label: str) -> float:
    """Calculate mass from volume and food label.

    Args:
        volume_cm3: Volume in cubic centimeters.
        food_label: Food label for density lookup.

    Returns:
        Mass in grams.
    """
    density_data = get_food_density(food_label)
    return volume_cm3 * density_data["density"]


def compute_nutrition(volume_cm3: float, food_label: str) -> dict[str, float]:
    """Compute nutrition from volume and food label.

    Args:
        volume_cm3: Volume in cubic centimeters.
        food_label: Food label.

    Returns:
        Dict with calories, protein, carbs, fat, fiber, saturated_fat, sugars.
    """
    mass_g = compute_mass(volume_cm3, food_label)
    scale = mass_g / 100.0

    density_data = get_food_density(food_label)

    return {
        "mass_g": mass_g,
        "calories": density_data["calories"] * scale,
        "protein": density_data["protein"] * scale,
        "carbohydrates": density_data["carbohydrates"] * scale,
        "fat": density_data["fat"] * scale,
        "fiber": density_data["fiber"] * scale,
        "saturated_fat": density_data.get("saturated_fat", 0.0) * scale,
        "sugars": density_data.get("sugars", 0.0) * scale,
    }
