---
status: investigating
trigger: "Investigate and fix CI failures for 'NutriSnap CI'."
created: 2025-05-14T10:00:00Z
updated: 2025-05-14T10:00:00Z
---

## Current Focus

hypothesis: Missing dependencies in requirements.txt and incorrect paths in tests are causing CI failures. Flake8 errors need to be addressed or ignored in config.
test: Check requirements.txt, verify file paths, and run linting locally.
expecting: Identify missing packages and path mismatches.
next_action: gather initial evidence

## Symptoms

expected: CI should pass all tests and linting.
actual: 
1. `ModuleNotFoundError`: Missing `aiosqlite`, `albumentations`, `loguru`, `sklearn`, `scikit-learn`, `python-jose`, `passlib`.
2. `FileNotFoundError`: Tests are looking for `src/nutrisnap/data/densities.json` but it's likely at `nutrisnap/data/densities.json` relative to the `backend/` root.
3. Flake8 errors: Line length (E501), whitespace before colon (E203), imports not at top (E402).
errors: 
- `ModuleNotFoundError: No module named 'aiosqlite'`
- `FileNotFoundError: [Errno 2] No such file or directory: 'src/nutrisnap/data/densities.json'`
- `backend/app/auth.py:13:80: E501 line too long (83 > 79 characters)`
reproduction: 
- `cd backend; pip install -r requirements.txt; pytest tests/`
started: Started after recent project restructuring and linting fixes.

## Eliminated

## Evidence

## Resolution

root_cause: 
fix: 
verification: 
files_changed: []
