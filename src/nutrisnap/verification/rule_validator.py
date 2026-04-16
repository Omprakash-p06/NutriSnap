"""Rule-based nutrition output validator for NutriSnap.

Applies hard physiological bounds and calorie-macro consistency checks
before predictions are returned to API consumers.
"""
from dataclasses import dataclass, field

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    valid: bool
    confidence: float  # 0.0–1.0 (1.0 = fully passes all checks)
    flagged_reason: str | None = None
    flags: list[str] = field(default_factory=list)


class NutritionValidator:
    """Hard bounds + calorie-macro consistency check.

    Bounds (from plan spec):
        Calories:      50–1,500 kcal
        Protein:        1–150 g
        Carbohydrates:  1–250 g
        Fat:            1–80 g

    Consistency:
        |predicted_calories - (4*protein + 4*carbs + 9*fat)| > 20% of predicted_calories
        → flagged as inconsistent

    Args:
        calorie_bounds:  (min, max) kcal
        protein_bounds:  (min, max) g
        carb_bounds:     (min, max) g
        fat_bounds:      (min, max) g
        consistency_threshold: Relative tolerance for macro-calorie check (default 0.20)
    """

    def __init__(
        self,
        calorie_bounds: tuple[float, float] = (50.0, 1500.0),
        protein_bounds: tuple[float, float] = (1.0, 150.0),
        carb_bounds: tuple[float, float] = (1.0, 250.0),
        fat_bounds: tuple[float, float] = (1.0, 80.0),
        consistency_threshold: float = 0.20,
    ):
        self.calorie_bounds = calorie_bounds
        self.protein_bounds = protein_bounds
        self.carb_bounds = carb_bounds
        self.fat_bounds = fat_bounds
        self.consistency_threshold = consistency_threshold

    def validate(self, prediction: dict) -> ValidationResult:
        """Validate a nutrition prediction dict.

        Args:
            prediction: dict with keys:
                'calories'  (float) kcal
                'protein'   (float) g
                'carbs'     (float) g
                'fat'       (float) g

        Returns:
            ValidationResult with valid flag, confidence score, and flags list.
        """
        calories = float(prediction.get("calories", 0))
        protein = float(prediction.get("protein", 0))
        carbs = float(prediction.get("carbs", 0))
        fat = float(prediction.get("fat", 0))

        flags: list[str] = []

        # --- Hard bounds ---
        if not (self.calorie_bounds[0] <= calories <= self.calorie_bounds[1]):
            flags.append(
                f"Calories {calories:.1f} kcal outside bounds "
                f"[{self.calorie_bounds[0]}, {self.calorie_bounds[1]}]"
            )
        if not (self.protein_bounds[0] <= protein <= self.protein_bounds[1]):
            flags.append(
                f"Protein {protein:.1f}g outside bounds "
                f"[{self.protein_bounds[0]}, {self.protein_bounds[1]}]"
            )
        if not (self.carb_bounds[0] <= carbs <= self.carb_bounds[1]):
            flags.append(
                f"Carbs {carbs:.1f}g outside bounds "
                f"[{self.carb_bounds[0]}, {self.carb_bounds[1]}]"
            )
        if not (self.fat_bounds[0] <= fat <= self.fat_bounds[1]):
            flags.append(
                f"Fat {fat:.1f}g outside bounds "
                f"[{self.fat_bounds[0]}, {self.fat_bounds[1]}]"
            )

        # --- Macro-calorie consistency ---
        macro_calories = 4.0 * protein + 4.0 * carbs + 9.0 * fat
        if calories > 0:
            relative_error = abs(calories - macro_calories) / calories
            if relative_error > self.consistency_threshold:
                flags.append(
                    f"Macro-calorie inconsistency: predicted={calories:.1f} kcal "
                    f"vs macro-derived={macro_calories:.1f} kcal "
                    f"(relative error={relative_error:.1%})"
                )

        # --- Confidence score ---
        # Simple linear penalty: start at 1.0, subtract per flag
        confidence = max(0.0, 1.0 - 0.25 * len(flags))

        valid = len(flags) == 0
        flagged_reason = "; ".join(flags) if flags else None

        if flags:
            logger.debug(f"Validation flags: {flags}")

        return ValidationResult(
            valid=valid,
            confidence=confidence,
            flagged_reason=flagged_reason,
            flags=flags,
        )
