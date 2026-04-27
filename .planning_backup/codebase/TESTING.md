# Testing Strategy

**Refresh Date:** 2026-04-27

## Overview
The testing strategy focuses on ensuring accuracy in nutritional predictions while maintaining a stable API and a responsive frontend.

## Backend Testing
- **Unit Tests:** Located in `tests/unit/`. Target individual components like `merger.py` or `validator.py`.
- **Integration Tests:** Located in `tests/integration/`. Test the full `InferencePipeline` with sample images.
- **Accuracy Benchmarks:**
  - Metric: Mean Absolute Error (MAE) in kcal.
  - Goal: MAE ≤ 40 kcal for the 10-dish MVP subset.
  - Tooling: Custom scripts in `reports/` to generate accuracy tables.

## Frontend Testing
- **Manual Verification:** Use of the browser tool to verify UI responsiveness and view transitions.
- **PWA Validation:** Checking service worker registration and manifest validity.
- **Component isolation:** Testing individual components like `ProgressRing` with mock props.

## Automated Testing (CI)
- **GitHub Actions:** Runs on every push to `main` or PR.
  - Linting (Flake8, ESLint).
  - Basic unit tests.
  - Build verification (Vite).

## Manual Verification Steps
1. Start backend: `uvicorn nutrisnap.api.main:app`.
2. Start frontend: `npm run dev`.
3. Perform end-to-end scan:
   - Upload image.
   - Wait for processing.
   - Verify nutrition card contents.
