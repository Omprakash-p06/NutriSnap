"""Quick test of densities module."""

from nutrisnap.data.densities import load_density_db, get_food_density

# Load database
db = load_density_db()
foods_count = len(db.get("foods", {}))
print(f"Loaded {foods_count} foods")

# Get chicken
chicken = get_food_density("chicken")
print(f"Chicken: density={chicken['density']}, protein={chicken['protein']}g/100g")

# Get rice
rice = get_food_density("rice")
print(f"Rice: density={rice['density']}, carbs={rice['carbohydrates']}g/100g")

# Test unknown food
unknown = get_food_density("unknown_food_xyz")
print(f"Unknown food fallback: density={unknown['density']}")

print("All tests passed!")