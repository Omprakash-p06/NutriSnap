---
status: investigating
trigger: "Investigate issue: ci-structure-mismatch-and-lint"
created: 2025-05-14T12:00:00Z
updated: 2025-05-14T12:00:00Z
---

## Current Focus

hypothesis: CI workflows are using outdated root paths instead of the new `backend/` directory structure.
test: Examine `.github/workflows/*.yml` and compare paths with actual file locations.
expecting: Discrepancies between workflow paths and filesystem structure.
next_action: gather initial evidence

## Symptoms

expected: CI jobs (test, lint, backend-lint-test) should pass.
actual: 
- `test (3.10)` fails because it can't find `requirements.txt` at the root.
- `lint` fails because it can't find `src/` at the root for `black`.
- `backend-lint-test` fails with 57 ruff errors (unused imports, etc.).
errors: 
- `ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'`
- `Error: Invalid value for 'SRC ...': Path 'src/' does not exist.`
- 57 linting errors in `backend/`.
reproduction: 
- Run `pip install -r requirements.txt` at root (fails).
- Run `black src/` at root (fails).
- Run `ruff check .` inside `backend/` (reports 57 errors).
started: Started today, likely after moving code into `backend/` and `frontend/` folders without updating CI.

## Eliminated

<!-- APPEND only - prevents re-investigating -->

## Evidence

- timestamp: 2025-05-14T12:10:00Z
  checked: .github/workflows/*.yaml and filesystem structure
  found: test.yaml and lint.yaml are pointing to root-level paths (src/, requirements.txt, etc.) which no longer exist at the root. backend/ has its own requirements.txt and code structure.
  implication: CI workflows need to be updated to target the backend/ directory.

- timestamp: 2025-05-14T12:15:00Z
  checked: backend/ directory linting
  found: 57 ruff errors in backend/, including unused imports, module-level imports not at top of file, ambiguous variable names, and multiple statements on one line.
  implication: Need to run ruff --fix and manually fix remaining linting errors in backend/.

## Resolution

root_cause: 
fix: 
verification: 
files_changed: []
