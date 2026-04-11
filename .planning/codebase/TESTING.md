# Testing Patterns

**Analysis Date:** 2026-04-11

**Mapping basis:** This repo currently documents setup and manual flows, but `HEAD` does not contain a real test suite. This file records the actual testing posture so future planning does not assume coverage that is not there.

## Test Framework

**Runner status:**
- Python testing dependencies exist in `requirements.txt`: `pytest` and `pytest-asyncio`
- Frontend `frontend/package.json` has no test runner dependency or `test` script
- No `tests/`, `__tests__/`, `*.test.py`, or `*.test.ts(x)` files were found in `HEAD`

**Run commands currently available:**
```bash
pytest
python ml/train_yolo.py --validate
uvicorn backend.main:app --reload
npm run lint --prefix frontend
npm run build --prefix frontend
```

## Test File Organization

**Current state:**
- No formal test tree exists
- No fixtures directory, no coverage config, and no CI workflow were found

**Closest things to verification helpers:**
- `ml/train_yolo.py` includes a `validate_model()` command for model evaluation
- `scripts/setup_db.py` attempts to seed sample data for local development
- `ai_engine/agents/detection_agent.py` falls back to `_mock_detection()` when a YOLO model is unavailable

## Test Structure

**Observed practice:**
- Verification is mostly manual and developer-driven
- `README.md` describes running the backend and frontend locally, implying smoke testing through the UI
- API behavior can be checked through FastAPI docs at `/docs`

**What is missing:**
- No unit test structure (`describe`, `pytest` functions, fixtures, etc.)
- No integration tests for the scan -> analyze -> save meal flow
- No regression tests for training scripts or schema compatibility

## Mocking

**Existing code-level fallback patterns:**
- `DetectionAgent._mock_detection()` provides hard-coded detections for development
- `PortionAgent` falls back to heuristic estimation when the XGBoost model is unavailable
- `Home.tsx` falls back to mock dashboard stats if backend loading fails

**Implication:**
- The codebase prefers runtime fallbacks over dedicated mocks in a test harness
- Those fallbacks are useful for manual demos but do not replace automated tests

## Fixtures and Factories

**Ad hoc data generation patterns:**
- `ml/train_portion.py` generates synthetic training data through `create_synthetic_data()`
- `scripts/setup_db.py` tries to seed sample records for local development
- Nutrition constants are embedded directly in `backend/services/nutrition_service.py`

**Gap:**
- No reusable fixture/factory module exists for backend, frontend, or ML testing

## Coverage

**Requirements:**
- No coverage target is defined
- No coverage command or configuration file is present

**Risk from current state:**
- Route contract changes, ORM drift, and ML fallback behavior can break silently
- The current large worktree deletion would be hard to validate automatically

## Test Types

**Unit tests:**
- None committed
- Highest-value future targets: `backend/services/nutrition_service.py`, `ai_engine/agents/portion_agent.py`, and `backend/routes/meals.py`

**Integration tests:**
- None committed
- Highest-value future target: scan/upload request through `backend/routes/food.py` with model stubs

**Frontend tests:**
- None committed
- No React Testing Library, Vitest, or Playwright setup exists

## Practical Verification Guidance For Future Work

- Use `pytest` for backend and ML utilities when adding automated tests
- Add API integration tests around `backend/main.py` and router behavior before refactoring routes
- Add a frontend test runner only if UI work resumes; current branch may be pivoting toward retraining
- Treat manual smoke testing as the current baseline, not as sufficient long-term verification

---
*Testing analysis: 2026-04-11*
*Update once real automated tests or CI pipelines are added*
