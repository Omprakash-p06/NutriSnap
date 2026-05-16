# NutriSnap Codebase Guide

This document provides a detailed overview of the important files and their roles in the NutriSnap architecture.

## 1. Project Overview
NutriSnap is a monorepo consisting of a **Python/FastAPI backend** and a **React/Vite frontend**. The system uses a multi-stage Computer Vision pipeline to estimate nutrition from meal photos.

---

## 2. Backend (Python/FastAPI)

Located in the `backend/` directory.

### Core Entry & Infrastructure
- `app/main.py`: The FastAPI application entry point. Handles lifespan (startup/shutdown), middleware (CORS, Rate Limiting), and registers all routers.
- `app/database.py`: Manages the asynchronous connection to the **SQLite** database (`nutrisnap.db`) using `aiosqlite`.
- `app/auth.py`: JWT-based authentication utilities, password hashing (bcrypt), and the `get_current_user` dependency for protected routes.

### API Routers (`app/routers/`)
- `auth.py`: User registration (`/signup`) and login (`/login`).
- `users.py`: User profile management and onboarding data.
- `prediction.py`: The main entry for scanning meal photos. Triggers the background inference task.
- `logs.py`: CRUD operations for daily meal history.
- `water.py`: Hydration tracking (logging and retrieving today's intake).
- `chat.py`: **WebSocket** endpoint for the AI Nutritionist ChatBot.
- `insights.py`: AI-generated coaching tips and daily highlights.
- `planning.py`: Personalized meal suggestions and nutrition plans.
- `health.py`: Liveness and database connectivity checks.

### Services & Logic (`app/services/`)
- `orchestrator.py`: **SequentialOrchestrator** — The "brain" of the ML pipeline. It loads and runs the CV models sequentially to fit in 4GB VRAM.
- `mapping.py`: **IngredientMappingService** — Fuzzy matches detected labels to the internal food database using `thefuzz`.
- `task_manager.py`: Manages the state and cleanup of background prediction jobs.

### ML Pipeline (`nutrisnap/`)
- `pipeline/merger.py`: Combines detection masks and depth maps to estimate volume, then converts it to mass using `densities.json`.
- `verification/llm_service.py`: A unified gateway for calling LLMs (Gemini, OpenRouter) with automatic provider fallback.
- `verification/llm_validator.py`: Uses an LLM to check if a meal's total volume and combination of items are realistic.

---

## 3. Frontend (React 19 + Vite)

Located in the `frontend/` directory.

### Core Architecture
- `src/App.jsx`: Main application shell with providers for Auth, Theme, and Routing.
- `src/context/AuthContext.jsx`: Manages global state including JWT tokens, user profile, and the active scan result.
- `src/services/api.js`: Centralized API service using `fetch` with pre-configured auth headers.

### Pages & Layout
- `src/pages/Home.jsx`: The primary dashboard page. Switches between "Scan", "Search", and "Chat" modes.
- `src/components/layout/LandingPage.jsx`: High-performance landing page with 3D models and system stats.
- `src/components/layout/Navbar.jsx`: Global navigation, gamification levels, and logout.

### Key Components
- `src/components/scanning/MultiFoodDisplay.jsx`: Renders the detailed cards for each detected food item after a scan.
- `src/components/dashboard/HydrationWidget.jsx`: Interactive water tracking with wave animations.
- `src/components/dashboard/InsightCards.jsx`: Carousel of AI coaching tips.
- `src/components/ChatBot.jsx`: Floating chat interface for real-time AI nutrition advice.

---

## 4. System Interaction Flow

1.  **Authentication:** User logs in via `frontend/src/services/api.js` -> `backend/app/routers/auth.py`. JWT is stored in `localStorage`.
2.  **Meal Scanning:**
    - User uploads photo in `Home.jsx`.
    - Frontend calls `/api/predict/` in `prediction.py`.
    - Backend starts a task in `SequentialOrchestrator`.
    - **Pipeline Stages:** Preprocess -> OWL-ViT (Detect) -> SAM 2 (Segment) -> GLPN (Depth) -> Merger (Nutrition) -> LLM (Validate).
    - Frontend polls the status until `PipelineResult` is ready.
3.  **Chat:** `ChatBot.jsx` connects via WebSocket to `chat.py`. The backend injects user profile context (height, weight, TDEE) into the LLM prompt for personalized advice.
