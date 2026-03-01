"""Health Metrics Service.

Provides BMI, BMR, and TDEE calculations.
"""

from enum import Enum


class ActivityLevel(str, Enum):
    """Activity level multipliers for TDEE calculation."""

    SEDENTARY = "sedentary"  # Little or no exercise
    LIGHT = "light"  # Light exercise 1-3 days/week
    MODERATE = "moderate"  # Moderate exercise 3-5 days/week
    ACTIVE = "active"  # Hard exercise 6-7 days/week
    VERY_ACTIVE = "very_active"  # Very hard exercise, physical job


# Activity level multipliers for TDEE
ACTIVITY_MULTIPLIERS = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.ACTIVE: 1.725,
    ActivityLevel.VERY_ACTIVE: 1.9,
}


class MetricsService:
    """Service for health metrics calculations.

    Provides BMI, BMR (Basal Metabolic Rate), and
    TDEE (Total Daily Energy Expenditure) calculations.
    """

    @staticmethod
    def calculate_bmi(weight_kg: float, height_cm: float) -> float:
        """Calculate Body Mass Index (BMI).

        Args:
            weight_kg: Weight in kilograms.
            height_cm: Height in centimeters.

        Returns:
            BMI value.

        Raises:
            ValueError: If height is zero or negative.
        """
        if height_cm <= 0:
            raise ValueError("Height must be positive")

        height_m = height_cm / 100
        return round(weight_kg / (height_m**2), 1)

    @staticmethod
    def get_bmi_category(bmi: float) -> str:
        """Get BMI category from BMI value.

        Args:
            bmi: BMI value.

        Returns:
            BMI category string.
        """
        if bmi < 18.5:
            return "Underweight"
        if bmi < 25:
            return "Normal"
        if bmi < 30:
            return "Overweight"
        return "Obese"

    @staticmethod
    def calculate_bmr(
        weight_kg: float,
        height_cm: float,
        age: int,
        is_male: bool = True,
    ) -> float:
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.

        Args:
            weight_kg: Weight in kilograms.
            height_cm: Height in centimeters.
            age: Age in years.
            is_male: Whether the person is male.

        Returns:
            BMR in kcal/day.
        """
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)

        if is_male:
            bmr += 5
        else:
            bmr -= 161

        return round(bmr, 0)

    @staticmethod
    def calculate_tdee(
        bmr: float,
        activity_level: str = "moderate",
    ) -> float:
        """Calculate Total Daily Energy Expenditure.

        Args:
            bmr: Basal Metabolic Rate in kcal/day.
            activity_level: Activity level string.

        Returns:
            TDEE in kcal/day.
        """
        try:
            level = ActivityLevel(activity_level.lower())
        except ValueError:
            level = ActivityLevel.MODERATE

        multiplier = ACTIVITY_MULTIPLIERS.get(level, 1.55)
        return round(bmr * multiplier, 0)

    @staticmethod
    def calculate_daily_target(  # pylint: disable=too-many-arguments
        weight_kg: float,
        height_cm: float,
        age: int,
        *,
        is_male: bool = True,
        activity_level: str = "moderate",
        goal: str = "maintain",
    ) -> int:
        """Calculate recommended daily calorie target.

        Args:
            weight_kg: Weight in kilograms.
            height_cm: Height in centimeters.
            age: Age in years.
            is_male: Whether the person is male.
            activity_level: Activity level string.
            goal: Weight goal (lose/maintain/gain).

        Returns:
            Recommended daily calories.
        """
        bmr = MetricsService.calculate_bmr(weight_kg, height_cm, age, is_male)
        tdee = MetricsService.calculate_tdee(bmr, activity_level)

        # Adjust based on goal
        if goal == "lose":
            return int(tdee - 500)  # 500 kcal deficit for ~0.5kg/week loss
        if goal == "gain":
            return int(tdee + 300)  # 300 kcal surplus for lean gain

        return int(tdee)  # Maintenance
