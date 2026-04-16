---
status: resolved
trigger: "ModuleNotFoundError: No module named 'requests' when running scripts/setup_foodsam.py"
symptoms:
  expected: "Setup script downloads SAM weights."
  actual: "Fails with ModuleNotFoundError."
  error_messages: "ModuleNotFoundError: No module named 'requests'"
  timeline: "Part of the FoodSAM setup process."
  reproduction: "python scripts/setup_foodsam.py"
created: 2026-04-15
updated: 2026-04-15
---

# Setup FoodSAM Dependency Issue

## Root Cause
The `requests` library is used in `scripts/setup_foodsam.py` for downloading weights but was not included in `requirements.txt` or the environment.

## Resolution
- Added `requests>=2.31.0` to `requirements.txt`.
- Installed `requests` in the local environment using `.venv\Scripts\pip`.

## Verification
- Successfully ran `python scripts/setup_foodsam.py`. The script is currently downloading the SAM weights (2.4 GB).
