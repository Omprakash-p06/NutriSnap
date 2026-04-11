# Coding Conventions

**Analysis Date:** 2026-04-11

**Mapping basis:** These conventions are inferred from representative files in `HEAD`, especially `backend/main.py`, `backend/routes/*.py`, `ai_engine/*.py`, and `frontend/src/**/*.tsx`. The codebase is prototype-heavy, so some inconsistencies exist; use the dominant patterns below when extending committed code.

## Naming Patterns

**Files:**
- Python modules use `snake_case.py` (`nutrition_service.py`, `detection_agent.py`)
- React components and route pages use `PascalCase.tsx` (`Home.tsx`, `FoodResults.tsx`, `Navbar.tsx`)
- Frontend utility/API files use lower-case names (`client.ts`, `food.ts`, `meals.ts`)
- Python packages use `__init__.py` for package boundaries

**Functions:**
- Python functions and methods use `snake_case`
- React event handlers use `handleX` naming (`handleCapture`, `handleSaveMeal`, `handleDeleteMeal`)
- Async route handlers and data loaders use descriptive verbs (`analyze_food_image`, `loadDashboardData`)

**Variables:**
- Local variables use `snake_case` in Python and `camelCase` in TypeScript
- Constants use `UPPER_SNAKE_CASE` in Python (`FOOD_CLASSES`, `NUTRITION_DB`, `COUNT_BASED_FOODS`)
- Private-ish attributes use a leading underscore in Python for lazy-loaded members (`_model`, `_depth_model`)

**Types / Classes:**
- Python classes use `PascalCase` (`FoodAnalysisCoordinator`, `NutritionService`, `MealResponse`)
- TypeScript interfaces and types use `PascalCase` (`NutritionInfo`, `AnalysisResponse`)

## Code Style

**Formatting:**
- Python code uses docstrings on modules, classes, and many functions
- Python functions are heavily type-annotated
- TypeScript/React files use single quotes and semicolons
- JSX files in `HEAD` commonly use 4-space indentation inside components

**Linting:**
- Frontend linting is configured in `frontend/eslint.config.js`
- Python dev tools are listed in `requirements.txt`: `black`, `isort`, `mypy`, `pylint`
- No committed root config for Python lint/format tools was found, so conventions are more implicit than enforced

## Import Organization

**Python order:**
1. Standard library imports
2. Third-party imports
3. Local package imports

**TypeScript order:**
1. External packages
2. Local component / API imports
3. `import type` for local types when used

**Grouping:**
- Files generally use blank lines between import groups
- Relative imports are preferred inside the frontend (`../components/...`, `./client`)
- Python uses absolute package imports from repo packages (`from backend...`, `from ai_engine...`)

## Error Handling

**Patterns:**
- Backend routes raise `HTTPException` for expected validation/not-found failures
- Broad `try/except Exception` blocks are used around ML-heavy code paths like `backend/routes/food.py`
- Frontend async flows catch errors, log to console, and surface simple UI messages or alerts

**Logging:**
- No shared logger abstraction exists
- Backend uses `traceback.print_exc()` and simple prints in scripts
- Frontend uses `console.error(err)` in page components

## Comments and Documentation

**When comments appear:**
- Python relies more on docstrings than inline comments
- Inline comments are used to explain pipeline steps, fallback behavior, or UI sections
- JSX comments label layout regions (`Header`, `Quick Action`, `Stats Grid`)

**Documentation style:**
- Public-facing Python functions often include `Args` / `Returns` sections in docstrings
- TypeScript relies more on readable names plus occasional short JSDoc blocks in API wrappers

## Function Design

**Patterns:**
- Many Python methods are small, single-purpose helpers (`extract_depth_features`, `get_available_classes`)
- Coordinator/route functions orchestrate multiple steps but still prefer early returns for guard cases
- TypeScript page components keep side effects in local async helper functions inside the component

**Parameters / returns:**
- Python often uses explicit return types and optional parameters with defaults
- TypeScript favors typed request/response interfaces and object literals over tuples

## Module Design

**Exports:**
- React pages/components use `export default`
- Frontend API modules use named exports plus an optional default object export
- Python packages sometimes re-export via `__init__.py`, but direct module imports are common

**Boundaries to preserve:**
- Keep HTTP-specific logic in `backend/routes/`
- Keep persistence definitions in `backend/models/`
- Keep ML orchestration concerns in `ai_engine/` instead of route files

## Legacy / Prototype Notes

- Several files reflect rapid prototyping rather than hardened production standards
- Current branch deletions and `misc/` redesign docs suggest conventions may shift soon
- When in doubt, follow the patterns already present in the specific subsystem you touch

---
*Convention analysis: 2026-04-11*
*Update when linting or formatting rules become explicit across the repo*
