<!-- GSD:project-start source:PROJECT.md -->
## Project

**NutriSnap**

NutriSnap is a lightweight, production-oriented AI system that estimates calories, protein, carbohydrates, and fats from a single meal photo. The project is being rebuilt from an earlier proof-of-concept into a modular computer vision pipeline that combines research-backed external segmentation and volume-estimation components with a custom lightweight nutrition regressor and a FastAPI backend, all targeted at a GTX 1650 with 4GB VRAM.

The current project source of truth is the rebuild plan captured in `misc/ARCHITECTURE.md`, `misc/revised architecture.mermaid`, `misc/revised_implementationplan.md`, and `misc/implementation_changes.md`. The previously committed full-stack demo app is useful historical context, but it is no longer the target architecture.

**Core Value:** A user can upload a single meal image and receive a realistic nutrition estimate quickly enough for real-world use on commodity hardware.

### Constraints

- **Hardware**: GTX 1650 with 4GB VRAM — the architecture, training strategy, and third-party integrations must stay within consumer-grade GPU limits.
- **Performance**: Inference time must stay at or below 2 seconds per image — the system needs to feel usable, not just accurate offline.
- **Accuracy**: Target calorie MAE is <= 65 kcal and calorie MAPE is <= 30% — success is tied to useful nutritional estimates, not just qualitative demos.
- **Reliability**: No constant predictions and strong safeguards against overfitting — model behavior must remain believable and debuggable.
- **Architecture**: The solution must use a transparent modular pipeline, not a black-box end-to-end model — explainability and replaceability matter.
- **Deployment**: The deliverable must be a FastAPI backend suitable for production-style use — API design and runtime stability are required, not optional.
- **Dependencies**: External repositories must be integrated carefully and reproducibly — third-party code is a strength only if dependency management stays controlled.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.10+ - Backend API, AI inference, model training, and utility scripts in `backend/`, `ai_engine/`, `ml/`, and `scripts/`
- TypeScript 5.9 - Frontend application code in `frontend/src/`
- JavaScript (ES modules) - Frontend tooling config in `frontend/eslint.config.js`, `frontend/postcss.config.js`, and `frontend/tailwind.config.js`
- YAML and JSON - Model/data configuration in `configs/*.yaml` and nutrition/class data in `data/**/*.json`
- Markdown - Repo documentation in `README.md`, `misc/ARCHITECTURE.md`, and `misc/revised_implementationplan.md`
## Runtime
- Python application server via `uvicorn` running `backend.main:app`
- Browser runtime for the React single-page app mounted from `frontend/src/main.tsx`
- Local CPU-first ML inference; `README.md` explicitly says models are configured for CPU by default
- pip - Python dependencies are pinned loosely in `requirements.txt`
- npm - Frontend dependencies managed through `frontend/package.json`
- Lockfile: `frontend/package-lock.json` is present in `HEAD`
## Frameworks
- FastAPI 0.110+ - HTTP API and schema-driven request handling in `backend/main.py`
- SQLAlchemy 2.x - ORM and SQLite session management in `backend/database.py`
- Pydantic 2.x / pydantic-settings - API schemas and environment config in `backend/config.py`
- React 19.2 - Frontend UI in `frontend/src/`
- React Router DOM 7.13 - Client routing in `frontend/src/App.tsx`
- Ultralytics YOLO 8.x - Food detection in `ai_engine/agents/detection_agent.py` and `ml/train_yolo.py`
- XGBoost 2.x - Portion estimation model in `ai_engine/agents/portion_agent.py` and `ml/train_portion.py`
- Transformers 4.38+ - Depth Anything V2 depth estimation in `ai_engine/models/depth_model.py`
- OpenCV / NumPy / Pillow - Image preprocessing and CV utilities in `backend/services/preprocessing.py`
- Vite 7.3 - Frontend dev server and bundling
- TypeScript compiler - Frontend build step (`npm run build`)
- ESLint 9.x with `typescript-eslint` and React plugins - Frontend linting via `frontend/eslint.config.js`
- Docker / docker-compose - Local containerized backend and intended full-stack orchestration via `Dockerfile` and `docker-compose.yml`
## Key Dependencies
- `fastapi` - API routing and request validation
- `sqlalchemy` + `aiosqlite` - Local persistence using SQLite
- `ultralytics` - Detection model loading and inference
- `xgboost` + `joblib` - Portion estimation model training and loading
- `transformers` - Depth estimation model pipeline
- `axios` - Frontend HTTP client in `frontend/src/api/client.ts`
- `recharts` - Nutrition visualizations in dashboard components
- `python-multipart` - File uploads for `/api/v1/analyze`
- `uvicorn[standard]` - ASGI server
- `tailwindcss` + `postcss` + `autoprefixer` - Frontend styling pipeline
## Configuration
- Root `.env` is read by `backend/config.py`
- Frontend can use `frontend/.env` for `VITE_API_URL`
- Key backend vars: `DATABASE_URL`, `MODEL_PATH`, `CONFIDENCE_THRESHOLD`, `IMAGE_SIZE`, `ENV`
- `requirements.txt` - Python dependency manifest
- `frontend/package.json` - Frontend scripts and dependencies
- `frontend/vite.config.ts`, `frontend/tsconfig*.json`, `frontend/eslint.config.js`
- `configs/yolo_train.yaml` and `configs/portion_model.yaml` for training configuration
## Platform Requirements
- Windows/Linux/macOS can run the repo, but OpenCV system libraries are required in containers
- Node.js 18+ and Python 3.10+ are called out in `README.md`
- Local model weights are expected under `ml/weights/`
- Backend is designed to run in Docker from `Dockerfile`
- Frontend is a Vite SPA; `docker-compose.yml` expects a separate frontend image, although `HEAD` does not include `frontend/Dockerfile`
- Current branch state suggests a likely transition toward a retraining-focused architecture described in `misc/revised_implementationplan.md`
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- Python modules use `snake_case.py` (`nutrition_service.py`, `detection_agent.py`)
- React components and route pages use `PascalCase.tsx` (`Home.tsx`, `FoodResults.tsx`, `Navbar.tsx`)
- Frontend utility/API files use lower-case names (`client.ts`, `food.ts`, `meals.ts`)
- Python packages use `__init__.py` for package boundaries
- Python functions and methods use `snake_case`
- React event handlers use `handleX` naming (`handleCapture`, `handleSaveMeal`, `handleDeleteMeal`)
- Async route handlers and data loaders use descriptive verbs (`analyze_food_image`, `loadDashboardData`)
- Local variables use `snake_case` in Python and `camelCase` in TypeScript
- Constants use `UPPER_SNAKE_CASE` in Python (`FOOD_CLASSES`, `NUTRITION_DB`, `COUNT_BASED_FOODS`)
- Private-ish attributes use a leading underscore in Python for lazy-loaded members (`_model`, `_depth_model`)
- Python classes use `PascalCase` (`FoodAnalysisCoordinator`, `NutritionService`, `MealResponse`)
- TypeScript interfaces and types use `PascalCase` (`NutritionInfo`, `AnalysisResponse`)
## Code Style
- Python code uses docstrings on modules, classes, and many functions
- Python functions are heavily type-annotated
- TypeScript/React files use single quotes and semicolons
- JSX files in `HEAD` commonly use 4-space indentation inside components
- Frontend linting is configured in `frontend/eslint.config.js`
- Python dev tools are listed in `requirements.txt`: `black`, `isort`, `mypy`, `pylint`
- No committed root config for Python lint/format tools was found, so conventions are more implicit than enforced
## Import Organization
- Files generally use blank lines between import groups
- Relative imports are preferred inside the frontend (`../components/...`, `./client`)
- Python uses absolute package imports from repo packages (`from backend...`, `from ai_engine...`)
## Error Handling
- Backend routes raise `HTTPException` for expected validation/not-found failures
- Broad `try/except Exception` blocks are used around ML-heavy code paths like `backend/routes/food.py`
- Frontend async flows catch errors, log to console, and surface simple UI messages or alerts
- No shared logger abstraction exists
- Backend uses `traceback.print_exc()` and simple prints in scripts
- Frontend uses `console.error(err)` in page components
## Comments and Documentation
- Python relies more on docstrings than inline comments
- Inline comments are used to explain pipeline steps, fallback behavior, or UI sections
- JSX comments label layout regions (`Header`, `Quick Action`, `Stats Grid`)
- Public-facing Python functions often include `Args` / `Returns` sections in docstrings
- TypeScript relies more on readable names plus occasional short JSDoc blocks in API wrappers
## Function Design
- Many Python methods are small, single-purpose helpers (`extract_depth_features`, `get_available_classes`)
- Coordinator/route functions orchestrate multiple steps but still prefer early returns for guard cases
- TypeScript page components keep side effects in local async helper functions inside the component
- Python often uses explicit return types and optional parameters with defaults
- TypeScript favors typed request/response interfaces and object literals over tuples
## Module Design
- React pages/components use `export default`
- Frontend API modules use named exports plus an optional default object export
- Python packages sometimes re-export via `__init__.py`, but direct module imports are common
- Keep HTTP-specific logic in `backend/routes/`
- Keep persistence definitions in `backend/models/`
- Keep ML orchestration concerns in `ai_engine/` instead of route files
## Legacy / Prototype Notes
- Several files reflect rapid prototyping rather than hardened production standards
- Current branch deletions and `misc/` redesign docs suggest conventions may shift soon
- When in doubt, follow the patterns already present in the specific subsystem you touch
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- FastAPI monolith for API endpoints and persistence
- Co-located AI inference layer inside the same repo, imported directly by the backend
- Client-side React application with route-based pages and thin API wrappers
- Local SQLite persistence and local file/model storage instead of managed cloud services
- Separate training scripts under `ml/` alongside production inference code
## Layers
- Purpose: Render scan/history/dashboard/profile flows and collect user actions
- Contains: Route pages, presentational components, and API client wrappers in `frontend/src/`
- Depends on: Browser runtime, Axios client, backend HTTP routes
- Used by: End users in the browser
- Purpose: Expose HTTP endpoints, validate input, and shape responses
- Contains: `backend/main.py`, routers in `backend/routes/`, and Pydantic schemas in `backend/schemas/`
- Depends on: Database layer and AI orchestration layer
- Used by: Frontend SPA and any direct API callers
- Purpose: Store meals and expose nutrition/dashboard data
- Contains: SQLAlchemy setup in `backend/database.py`, ORM models in `backend/models/`, and some business utilities in `backend/services/`
- Depends on: SQLite and Pydantic schema contracts
- Used by: API routes
- Purpose: Run detection, portion estimation, and nutrition lookup as one pipeline
- Contains: `ai_engine/coordinator.py`, agent wrappers in `ai_engine/agents/`, and model wrappers in `ai_engine/models/`
- Depends on: Local model files, OpenCV/NumPy, and backend nutrition services
- Used by: `backend/routes/food.py`
- Purpose: Train and validate models, preprocess datasets, and manage training assets
- Contains: `ml/*.py`, `configs/*.yaml`, `scripts/*.py`, and static data under `data/`
- Depends on: Python ML stack and local datasets
- Used by: Developers and retraining workflows, not the live request path
## Data Flow
- Backend state is persistent only through SQLite (`data/nutrisnap.db`)
- Frontend state is page-local React state; there is no global store
- Temporary upload state lives on disk in `temp_uploads/` for the duration of a request
## Key Abstractions
- Purpose: Wrap one model/service responsibility behind a narrow interface
- Examples: `DetectionAgent`, `PortionAgent`, `NutritionAgent`
- Pattern: Lazy-loading service objects coordinated by `FoodAnalysisCoordinator`
- Purpose: Separate transport models from persistence models
- Examples: `backend/schemas/meal.py` vs `backend/models/meal.py`
- Pattern: Pydantic for API contracts, SQLAlchemy ORM for storage
- Purpose: Keep page components from embedding raw HTTP details
- Examples: `frontend/src/api/client.ts`, `frontend/src/api/food.ts`, `frontend/src/api/meals.ts`
- Pattern: Shared Axios client plus per-domain wrappers
## Entry Points
- Location: `backend/main.py`
- Triggers: `uvicorn backend.main:app --reload` or Docker CMD
- Responsibilities: Create app, attach CORS, register routers, and create tables on startup
- Location: `frontend/src/main.tsx` and `frontend/src/App.tsx`
- Triggers: Vite dev server or frontend build output
- Responsibilities: Mount React, configure routes, render shared navbar/layout
- Locations: `ml/train_yolo.py`, `ml/train_portion.py`, `scripts/setup_db.py`
- Triggers: Manual CLI execution by developers
- Responsibilities: Model training, validation, and database setup/seeding
## Error Handling
- `backend/routes/food.py` catches any exception, prints a traceback, and converts it to HTTP 500
- CRUD routes in `backend/routes/meals.py` use direct 404 checks for missing records
- Frontend pages catch async errors, set local error state, and sometimes fall back to `alert()` or mock values
## Cross-Cutting Concerns
- Pydantic models define response/request structure
- File upload validation is limited to content type checks in `backend/routes/food.py`
- There is no backend auth layer in `HEAD`
- Frontend token plumbing exists, but it is not connected to server-side authorization
- Mostly ad hoc via `print`, `traceback`, and browser console logs
- No shared logger, request correlation, or observability layer
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
