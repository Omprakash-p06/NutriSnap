# Architecture

**Analysis Date:** 2025-05-15

## Pattern Overview

**Overall:** Modular Monolith with separate Frontend and Backend.

**Key Characteristics:**
- API-first design (FastAPI)
- Pipeline-based ML inference
- Component-based Frontend (React)

## Layers

**Frontend Layer:**
- Purpose: User interface and PWA experience
- Location: `frontend/`
- Contains: React components, hooks, and services
- Depends on: Backend API
- Used by: End users

**API Layer:**
- Purpose: Entry point for client requests
- Location: `backend/app/`
- Contains: Routers, schemas, and middleware
- Depends on: Service Layer
- Used by: Frontend

**Service Layer:**
- Purpose: Business logic and ML orchestration
- Location: `backend/app/services/`
- Contains: Logic for food detection, volume estimation, and nutrition analysis
- Depends on: ML Core (`nutrisnap/`)
- Used by: API Layer

**ML Core:**
- Purpose: Heavy lifting for AI inference
- Location: `backend/nutrisnap/`
- Contains: Model wrappers and processing pipelines
- Depends on: PyTorch, Transformers, Ultralytics
- Used by: Service Layer

## Data Flow

**Food Scan Flow:**

1. Frontend sends image to `POST /api/scan`
2. API Layer validates request and passes image to Service Layer
3. Service Layer invokes ML Pipeline:
   - Detection (YOLO/OwlViT)
   - Segmentation (SAM 2)
   - Depth Estimation (GLPN)
   - Volume/Mass Estimation (Custom Regressor)
   - Nutritional Reasoning (Gemini or Local LLM)
4. Results are cached and returned to Frontend

**State Management:**
- Frontend: React Context and Hooks
- Backend: Stateless API with DiskCache for performance

## Key Abstractions

**ML Pipeline:**
- Purpose: Sequential execution of AI models
- Examples: `backend/nutrisnap/pipeline.py` (assumed based on structure)
- Pattern: Chain of Responsibility / Pipeline

**LLM Provider:**
- Purpose: Abstraction over cloud (Gemini) and local (llama.cpp) models
- Examples: `backend/nutrisnap/utils/local_llm_backend.py`
- Pattern: Strategy Pattern

## Entry Points

**Backend API:**
- Location: `backend/app/main.py`
- Triggers: HTTP Requests
- Responsibilities: Server initialization, middleware attachment, router registration

**Frontend App:**
- Location: `frontend/src/main.jsx`
- Triggers: Browser load
- Responsibilities: React mounting, PWA registration

**Setup/Start Scripts:**
- Location: `setup.py`, `start.py`
- Triggers: Developer execution
- Responsibilities: Environment preparation and service orchestration

## Error Handling

**Strategy:** Centralized exception handling in Backend; Error Boundaries and Toast notifications in Frontend.

**Patterns:**
- FastAPI Exception Handlers: `backend/app/exceptions.py`
- Try-Except blocks in ML pipelines with fallback mechanisms

## Cross-Cutting Concerns

**Logging:** Loguru in backend for structured logs
**Validation:** Pydantic models in backend; Prop-types/TypeScript (if applicable) in frontend
**Authentication:** JWT-based middleware in `backend/app/middleware.py`

---

*Architecture analysis: 2025-05-15*
