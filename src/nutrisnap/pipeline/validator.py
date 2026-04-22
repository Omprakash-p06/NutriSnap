"""Nutrition Validator for NutriSnap.

Performs rule-based checks on nutrition predictions to ensure physical
and biochemical plausibility.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple

import yaml


class NutritionValidator:
    """Validator using Atwater factors and physical density gates."""

    def __init__(self, config_path: str | Path = "configs/pipeline/validator.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)["validator"]

    def validate(
        self,
        predictions: Dict[str, float],
        volume_cm3: float,
        area_cm2: float,
        confidence: float = 1.0,
    ) -> Tuple[bool, Optional[str]]:
        """Validate predictions against physical and biological constraints.

        Args:
            predictions: Dict with 'calories', 'fat', 'carbs', 'protein'.
            volume_cm3: Estimated food volume.
            area_cm2: Estimated food surface area.
            confidence: Model confidence score.

        Returns:
            Tuple of (is_plausible, failure_reason).
        """
        # 1. Confidence Check
        if confidence < self.config["min_confidence"]:
            return False, f"Low model confidence: {confidence:.2f}"

        # 2. Extract values
        kcal = predictions.get("calories", 0)
        fat = predictions.get("fat", 0)
        carbs = predictions.get("carbs", 0)
        prot = predictions.get("protein", 0)

        # 3. Atwater Consistency Check (4-4-9)
        # 4*P + 4*C + 9*F should be close to kcal
        calculated_kcal = (4 * prot) + (4 * carbs) + (9 * fat)
        if kcal > 0:
            diff_ratio = abs(kcal - calculated_kcal) / kcal
            if diff_ratio > self.config["atwater_tolerance"]:
                return (
                    False,
                    f"Atwater inconsistency (diff {diff_ratio:.1%}): Predicted={kcal:.1f}, Calculated={calculated_kcal:.1f}",
                )

        # 4. Energy Density Check (kcal / cm3)
        if volume_cm3 > 0:
            density = kcal / volume_cm3
            if density < self.config["density_min"]:
                return False, f"Energy density too low: {density:.3f} kcal/cm3"
            if density > self.config["density_max"]:
                return False, f"Energy density too high: {density:.2f} kcal/cm3"

        # 5. Geometric Sanity
        if area_cm2 > 0:
            avg_height = volume_cm3 / area_cm2
            if avg_height < self.config["height_min"]:
                return (
                    False,
                    f"Geometric anomaly: Object too flat ({avg_height:.2f}cm avg height)",
                )
            if avg_height > self.config["height_max"]:
                return (
                    False,
                    f"Geometric anomaly: Object too tall ({avg_height:.1f}cm avg height)",
                )

        return True, None
