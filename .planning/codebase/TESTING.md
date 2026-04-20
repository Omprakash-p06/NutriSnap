# Testing Patterns

**Analysis Date:** 2026-04-18

**Mapping basis:** This audit reflects the current automated test suite located in the `tests/` directory.

## Test Framework

**Core Runner:**
- **Pytest:** The primary test runner for the entire Python codebase.
- **Pytest-asyncio:** Enables testing of asynchronous FastAPI endpoints and `aiosqlite` store.

**Run Commands:**
- `pytest` - Run the full suite.
- `pytest tests/test_api.py` - Run specific module tests.
- `make test` - Automation command (if defined in Makefile).

## Test Organization

**Directory Structure:**
- `tests/` mirrors the `src/nutrisnap/` package structure where possible.
- **Unit Tests:** Focus on individual modules (e.g., `tests/test_utils.py`).
- **Integration Tests:** Verify interactions between components (e.g., `tests/test_pipeline.py`).
- **API Tests:** Test FastAPI endpoints and job lifecycle (e.g., `tests/test_api.py`).

**Key Test Files:**
- `test_api.py`: Core API functionality.
- `test_data.py`: Dataset loading and preprocessing.
- `test_models.py`: Model architecture and forward passes.
- `test_pipeline.py`: End-to-end inference pipeline logic.
- `test_validator.py`: Rule-based and USDA verification logic.

## Test Types & Coverage

**Unit Testing:**
- Extensive coverage of utility functions, data loaders, and individual model blocks.
- Mocks are used to isolate components from external dependencies (e.g., mocking the USDA API).

**Integration Testing:**
- Testing the flow from image ingestion to the final prediction result.
- Uses local test data/images located in `tests/data/` (if present).

**Regression Testing:**
- GitHub Workflows (`test.yaml`) ensure that new commits do not break existing functionality.

## Mocking & Fixtures

**Fixtures:**
- Pytest fixtures are used for common setup tasks like initializing the `ResultStore` with a temporary database or creating sample config objects.

**Mocking:**
- `unittest.mock` and `pytest-mock` are used to stub out:
    - External API calls (Gemini, USDA).
    - Large ML model loads during unit testing.
    - File system operations.

## Coverage Goals

- **Target:** Aim for >80% coverage on core business logic (pipeline, api, utils).
- **Inference logic:** High priority for ensuring consistent results across refactors.

## Continuous Integration

- **GitHub Actions:** Automatically runs the test suite on every push to `main` and all pull requests.
- **Environment:** CI environment mimics the production environment using the same `requirements.txt`.

---
*Testing analysis: 2026-04-18*
