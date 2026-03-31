# Codebase Structure

## Directory Layout
- `backend/`: FastAPI application code.
  - `routes/`: API endpoint definitions (food, meals, dashboard).
  - `services/`: Business logic separating routes from internal mechanisms.
  - `models/`: SQLAlchemy ORM definitions mapping tables in the database.
  - `schemas/`: Pydantic models for incoming payload validation and outgoing responses.
- `frontend/`: Output of typical Vite scaffolding with React/TypeScript.
  - `src/pages/`: Component groupings for the top-level paths (Scan, History, Home).
  - `src/components/`: Reusuable UI elements including dashboards and specific widgets.
  - `src/api/`: Pre-configured Axios functions corresponding to the backend API.
- `ai_engine/`: Specialized package specifically concerning ML workflows and inference.
  - `agents/`: Wrappers orchestrating individual steps of complex queries.
  - `models/`: Classes loading actual `.pt` and `.joblib` weights.
- `ml/`: Model training scripts, preprocessing, and exploratory tools. Not used in production server logic.
- `data/`: The local datastores. Contains both static JSON datasets mapping classes to nutritional facts and the interactive SQLite filesystem.
