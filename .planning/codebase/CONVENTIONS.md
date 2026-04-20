# Coding Conventions

**Analysis Date:** 2026-04-18

**Mapping basis:** These conventions are derived from the current standard Python package structure in `src/nutrisnap/`.

## Naming Patterns

**Files:**
- Python modules: `snake_case.py` (`nutrition_regressor.py`, `config_loader.py`).
- Configuration files: `snake_case.yaml` (`segmenter.yaml`).
- Package boundaries: `__init__.py`.

**Classes:**
- Always `PascalCase` (`InferencePipeline`, `NutriSnapDataset`, `JobWorker`).

**Functions & Methods:**
- Always `snake_case` (`get_prediction`, `process_job`, `initialize_models`).
- Private helpers start with a single underscore (`_load_config`).

**Variables:**
- Local variables: `snake_case`.
- Global constants: `UPPER_SNAKE_CASE` (`DEFAULT_CONFIDENCE`, `MAX_IMAGE_SIZE`).
- Instance members: `snake_case`.

**Type Hints:**
- All function signatures should be type-annotated using Python 3.10+ syntax (`int | None` instead of `Optional[int]`).

## Code Style

**Formatting:**
- **PEP 8:** Strict adherence to PEP 8 standards.
- **Black:** Used for automatic code formatting (88 characters per line).
- **Docstrings:** Required for all public classes and functions using Google style or ReStructuredText.

**Linting:**
- **Pylint / Flake8:** Used to enforce code quality.
- **Mypy:** Used for static type checking.
- **Isort:** Used to maintain consistent import ordering.

## Import Organization

**Standard Ordering:**
1. Standard library (e.g., `os`, `sys`, `pathlib`).
2. Third-party packages (e.g., `torch`, `fastapi`).
3. Internal package imports using absolute paths (`from nutrisnap.api.models import ...`).

**Grouping:**
- Blank lines between groups.
- Absolute imports preferred over relative imports.

## Error Handling

**Strategy:** Raise specific custom exceptions where possible and handle them at the top-level orchestrator or API boundary.

- **Custom Exceptions:** Defined in `src/nutrisnap/utils/exceptions.py`.
- **API Boundary:** FastAPI handles `HTTPException` for client responses.
- **Background Worker:** Catches and logs exceptions, updating the job status in the `ResultStore` with the error message.

## Logging

**Standard:**
- Use the built-in `logging` module.
- Get logger per module: `logger = logging.getLogger(__name__)`.
- Avoid `print()` for runtime diagnostics.
- Logging levels (DEBUG, INFO, WARNING, ERROR) used appropriately.

## Documentation

- **README.md:** Top-level project overview.
- **docs/:** In-depth technical guides.
- **In-code Docstrings:** Explain the 'why' and 'how' of complex logic.

## Function & Module Design

**Patterns:**
- **Composition over Inheritance:** Preferred for pipeline components and model blocks.
- **Dependency Injection:** Use for passing configurations and service objects (like `ResultStore`) to workers or pipelines.
- **Single Responsibility Principle:** Each module should have one clear purpose (e.g., `segmenter.py` only handles segmentation).

## Testing

- Every new feature or bug fix must include corresponding tests in `tests/`.
- Tests should follow the directory structure of the `src/` directory.

---
*Convention analysis: 2026-04-18*
