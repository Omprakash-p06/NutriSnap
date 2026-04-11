# Architecture

**Analysis Date:** 2026-04-11

**Mapping basis:** The architecture below is the committed design in `HEAD`. The current branch has most of those implementation files deleted locally, and `misc/ARCHITECTURE.md` plus `misc/revised_implementationplan.md` outline a likely future redesign. Keep that split in mind when planning new work.

## Pattern Overview

**Overall:** Full-stack monorepo with a local ML-powered backend and a separate React SPA frontend

**Key Characteristics:**
- FastAPI monolith for API endpoints and persistence
- Co-located AI inference layer inside the same repo, imported directly by the backend
- Client-side React application with route-based pages and thin API wrappers
- Local SQLite persistence and local file/model storage instead of managed cloud services
- Separate training scripts under `ml/` alongside production inference code

## Layers

**UI Layer:**
- Purpose: Render scan/history/dashboard/profile flows and collect user actions
- Contains: Route pages, presentational components, and API client wrappers in `frontend/src/`
- Depends on: Browser runtime, Axios client, backend HTTP routes
- Used by: End users in the browser

**API Layer:**
- Purpose: Expose HTTP endpoints, validate input, and shape responses
- Contains: `backend/main.py`, routers in `backend/routes/`, and Pydantic schemas in `backend/schemas/`
- Depends on: Database layer and AI orchestration layer
- Used by: Frontend SPA and any direct API callers

**Persistence / Domain Layer:**
- Purpose: Store meals and expose nutrition/dashboard data
- Contains: SQLAlchemy setup in `backend/database.py`, ORM models in `backend/models/`, and some business utilities in `backend/services/`
- Depends on: SQLite and Pydantic schema contracts
- Used by: API routes

**AI Orchestration Layer:**
- Purpose: Run detection, portion estimation, and nutrition lookup as one pipeline
- Contains: `ai_engine/coordinator.py`, agent wrappers in `ai_engine/agents/`, and model wrappers in `ai_engine/models/`
- Depends on: Local model files, OpenCV/NumPy, and backend nutrition services
- Used by: `backend/routes/food.py`

**Training / Offline Data Layer:**
- Purpose: Train and validate models, preprocess datasets, and manage training assets
- Contains: `ml/*.py`, `configs/*.yaml`, `scripts/*.py`, and static data under `data/`
- Depends on: Python ML stack and local datasets
- Used by: Developers and retraining workflows, not the live request path

## Data Flow

**Food Analysis Request:**
1. User captures or uploads an image in `frontend/src/pages/Scan.tsx`
2. `frontend/src/api/food.ts` posts multipart form data to `POST /api/v1/analyze`
3. `backend/routes/food.py` validates MIME type, writes a temp file, and offloads work to a threadpool
4. `ai_engine/coordinator.py` calls `DetectionAgent.detect()`, `PortionAgent.estimate_portion_with_unit()`, and `NutritionAgent.get_nutrition()`
5. The route maps raw results into Pydantic response objects and returns aggregate nutrition totals
6. The frontend optionally persists a meal via `POST /api/v1/meals`

**Dashboard / History Request:**
1. Home and history pages call `frontend/src/api/meals.ts`
2. Backend routes in `backend/routes/meals.py` and `backend/routes/dashboard.py` query SQLite through SQLAlchemy
3. ORM models are serialized through `backend/schemas/meal.py` and `backend/schemas/nutrition.py`
4. React components render summary cards, charts, and meal history lists

**Training Flow:**
1. Developers run scripts like `ml/train_yolo.py` or `ml/train_portion.py`
2. Config/data files under `configs/` and `data/` shape training inputs
3. Trained artifacts are written back to `ml/weights/` for later inference use

**State Management:**
- Backend state is persistent only through SQLite (`data/nutrisnap.db`)
- Frontend state is page-local React state; there is no global store
- Temporary upload state lives on disk in `temp_uploads/` for the duration of a request

## Key Abstractions

**Agent classes:**
- Purpose: Wrap one model/service responsibility behind a narrow interface
- Examples: `DetectionAgent`, `PortionAgent`, `NutritionAgent`
- Pattern: Lazy-loading service objects coordinated by `FoodAnalysisCoordinator`

**Schemas and models:**
- Purpose: Separate transport models from persistence models
- Examples: `backend/schemas/meal.py` vs `backend/models/meal.py`
- Pattern: Pydantic for API contracts, SQLAlchemy ORM for storage

**Thin frontend API modules:**
- Purpose: Keep page components from embedding raw HTTP details
- Examples: `frontend/src/api/client.ts`, `frontend/src/api/food.ts`, `frontend/src/api/meals.ts`
- Pattern: Shared Axios client plus per-domain wrappers

## Entry Points

**Backend server:**
- Location: `backend/main.py`
- Triggers: `uvicorn backend.main:app --reload` or Docker CMD
- Responsibilities: Create app, attach CORS, register routers, and create tables on startup

**Frontend bootstrap:**
- Location: `frontend/src/main.tsx` and `frontend/src/App.tsx`
- Triggers: Vite dev server or frontend build output
- Responsibilities: Mount React, configure routes, render shared navbar/layout

**Training / maintenance scripts:**
- Locations: `ml/train_yolo.py`, `ml/train_portion.py`, `scripts/setup_db.py`
- Triggers: Manual CLI execution by developers
- Responsibilities: Model training, validation, and database setup/seeding

## Error Handling

**Strategy:** Validate at the route boundary, raise `HTTPException` for expected failures, and use broad `try/except` blocks for inference/runtime failures

**Patterns:**
- `backend/routes/food.py` catches any exception, prints a traceback, and converts it to HTTP 500
- CRUD routes in `backend/routes/meals.py` use direct 404 checks for missing records
- Frontend pages catch async errors, set local error state, and sometimes fall back to `alert()` or mock values

## Cross-Cutting Concerns

**Validation:**
- Pydantic models define response/request structure
- File upload validation is limited to content type checks in `backend/routes/food.py`

**Authentication:**
- There is no backend auth layer in `HEAD`
- Frontend token plumbing exists, but it is not connected to server-side authorization

**Logging / diagnostics:**
- Mostly ad hoc via `print`, `traceback`, and browser console logs
- No shared logger, request correlation, or observability layer

---
*Architecture analysis: 2026-04-11*
*Update when the current restructure replaces the committed runtime architecture*
