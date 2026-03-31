# System Architecture

## High-Level Architecture
NutriSnap employs a decoupled client-server architecture consisting of a **React/TypeScript SPA Frontend** and a **Python/FastAPI Backend**.

## Flow sequence (Food Analysis Pipeline)
1. **User Request**: User uploads a food image.
2. **API Layer (`backend/routes/food.py`)**: Receives upload, writes file to a temporary location (`temp_uploads/`). Validates constraints.
3. **Execution Layer**: Dispatches the blocking AI operation `FoodAnalysisService.analyze_image` into a threadpool executor to avoid blocking the `asyncio` loop.
4. **Service Layer (`backend/services/food_analysis.py`)**: Responsible for connecting the HTTP layer with the raw AI components.
5. **AI Engine Coordinator (`ai_engine/coordinator.py`)**: Orchestrates the AI pipeline:
   - **Agent 1 (Detection)**: Uses YOLOv8 to identify food objects and bounding boxes.
   - **Agent 2 (Portion)**: Runs `depth-anything-v2` against the bounding box, then feeds the stats into an XGBoost model to get estimated grams.
   - **Agent 3 (Nutrition)**: Uses `nutrition_db` to convert portions into macro/micro nutrients.
6. **Delivery**: Converts raw dictionaries back into Pydantic models and returns JSON to the React client.

## Data Persistence
- **SQLAlchemy ORM** is used mapped to `data/nutrisnap.db`. Contains relationships between users, logged meals, and granular food items per meal.
