"""Direct test of merger module."""

import sys
from pathlib import Path

# Set up path
sys.path.insert(0, str(Path.cwd()))

# Test densities module directly (avoid package imports)
exec(open("nutrisnap/data/densities.py").read())

# Now test merger
from nutrisnap.pipeline.merger import (  # noqa: E402
    MultiFoodMerger,
    compute_mass,
    compute_nutrition,
)

# Test compute_mass
mass = compute_mass(100.0, "chicken")
print(f"100 cm3 chicken = {mass}g (expected ~104g)")

# Test compute_nutrition
nutrition = compute_nutrition(100.0, "chicken")
print(f"Nutrition: {nutrition}")

# Test simple merge
merger = MultiFoodMerger()
result = merger.merge_simple(
    labels=["chicken", "rice", "broccoli"], volumes_cm3=[100.0, 150.0, 50.0]
)

print(f"Merged {result.item_count} items")
print(f"Total: {result.total_calories:.1f} kcal, {result.total_protein:.1f}g protein")

print("Merger test passed!")
