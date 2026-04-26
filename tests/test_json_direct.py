"""Direct test of density JSON."""
import json
from pathlib import Path

db_path = Path("src/nutrisnap/data/densities.json")
with open(db_path) as f:
    db = json.load(f)

foods = len(db.get("foods", {}))
print(f"Loaded {foods} foods from JSON")

chicken = db["foods"].get("chicken")
print(f"Chicken: density={chicken['density']} g/cm3")

fallback = db.get("_fallback")
print(f"Fallback: {fallback}")

print("JSON test passed!")