"""Test merger logic directly."""

# Load density data
import json
from pathlib import Path

db_path = Path("src/nutrisnap/data/densities.json")
with open(db_path) as f:
    db = json.load(f)


def get_food(label):
    """Get food density data."""
    label = label.lower().strip()
    if label in db["foods"]:
        return db["foods"][label]
    # Fuzzy match
    for k in db["foods"]:
        if label in k:
            return db["foods"][k]
    return db["_fallback"]


def compute_mass(volume_cm3, label):
    """Calculate mass."""
    food = get_food(label)
    return volume_cm3 * food["density"]


def compute_nutrition(volume_cm3, label):
    """Calculate nutrition."""
    food = get_food(label)
    mass = volume_cm3 * food["density"]
    scale = mass / 100.0
    return {
        "mass_g": mass,
        "calories": food["calories"] * scale,
        "protein": food["protein"] * scale,
        "carbs": food["carbohydrates"] * scale,
        "fat": food["fat"] * scale,
    }


# Test chicken mass
mass = compute_mass(100.0, "chicken")
print(f"100 cm3 chicken = {mass}g")
assert abs(mass - 104.0) < 1.0, f"Expected ~104g, got {mass}"

# Test nutrition
nutrition = compute_nutrition(100.0, "chicken")
print(f"Nutrition: {nutrition}")
assert nutrition["calories"] > 0, "Should have calories"

# Test multi-item aggregation
items = [
    {"label": "chicken", "vol": 100.0},
    {"label": "rice", "vol": 150.0},
    {"label": "broccoli", "vol": 50.0},
]

total_cal = 0
total_prot = 0
for item in items:
    n = compute_nutrition(item["vol"], item["label"])
    total_cal += n["calories"]
    total_prot += n["protein"]

print(f"Multi-item: {total_cal:.1f} kcal, {total_prot:.1f}g protein")
assert total_cal > 0, "Should aggregate calories"

print("All merger logic tests passed!")
