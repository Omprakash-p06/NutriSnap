"""Rule-based nutrition output validator. Implement in Phase 5."""
class NutritionValidator:
    """Applies hard bounds and calorie-macro consistency checks."""
    CALORIE_BOUNDS = (50, 1500)
    PROTEIN_BOUNDS = (1, 150)
    CARB_BOUNDS = (1, 250)
    FAT_BOUNDS = (1, 80)
    def validate(self, prediction): raise NotImplementedError("Implement in Phase 5")

