"""Nutrition calculation utilities (Mifflin-St Jeor & TDEE)."""

ACTIVITY_MULTIPLIERS: dict[str, float] = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_ADJUSTMENTS: dict[str, float] = {
    "weight_loss": -500.0,
    "maintenance": 0.0,
    "muscle_gain": 300.0,
}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Mifflin-St Jeor Basal Metabolic Rate.

    Args:
        weight_kg: Body weight in kilograms.
        height_cm: Height in centimetres.
        age: Age in years.
        gender: 'male' or 'female'.

    Returns:
        BMR in kcal/day.
    """
    base = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age)
    return base + 5.0 if gender.lower() == "male" else base - 161.0


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Total Daily Energy Expenditure."""
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level.lower(), 1.2)
    return round(bmr * multiplier, 1)


def adjust_for_goal(tdee: float, goal: str) -> float:
    """Apply calorie surplus/deficit based on health goal."""
    adjustment = GOAL_ADJUSTMENTS.get(goal.lower(), 0.0)
    return round(tdee + adjustment, 1)


def macros_from_calories(target_calories: float) -> dict[str, float]:
    """Standard macro split: 25% protein, 45% carbs, 30% fat."""
    return {
        "protein_g": round(target_calories * 0.25 / 4, 1),
        "carbs_g": round(target_calories * 0.45 / 4, 1),
        "fat_g": round(target_calories * 0.30 / 9, 1),
    }
