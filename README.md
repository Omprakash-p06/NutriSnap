# NutriSnap

NutriSnap is an AI-powered nutrition tracking application. It allows users to take a photo of their food, automatically detects the food items (like dal, paneer, rice, roti), estimates portion sizes, and calculates nutritional content (calories, protein, carbs, fats).

## Project Structure

- `backend/`: FastAPI backend handling the API, database connectivity, and routing.
- `frontend/`: React + Vite + TypeScript frontend.
- `ai_engine/`: The core machine learning pipeline integrating YOLOv8 (detection), XGBoost (portion estimation), and Depth Anything V2.
- `ml/`: Model training scripts and data exploration tools.
- `data/`: SQLite database and internal data storage.

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** & **npm**

*(Note: The AI models are currently configured to run on CPU by default for maximum compatibility across devices.)*

---

## Setup & Run Instructions

To run the application, you need to start both the Python backend and the Node.js frontend in separate terminal windows.

### 1. Backend Setup

The backend runs the API and the AI inference engine.

**For Linux / macOS:**
```bash
# Navigate to the project root
cd NutriSnap

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Run the backend server
uvicorn backend.main:app --reload
```

**For Windows (PowerShell / CMD):**
```powershell
# Navigate to the project root
cd NutriSnap

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On PowerShell:
.\venv\Scripts\Activate.ps1
# On Command Prompt (CMD):
.\venv\Scripts\activate.bat

# Install requirements
pip install -r requirements.txt

# Run the backend server
uvicorn backend.main:app --reload
```

The backend API will be available at `http://localhost:8000`. You can view the interactive API documentation at `http://localhost:8000/docs`.

### 2. Frontend Setup

The frontend is a React application built with Vite and Tailwind CSS.

**For both Linux and Windows:**
```bash
# Open a new terminal window

# Navigate to the frontend directory
cd NutriSnap/frontend

# Install Node.js dependencies
npm install

# Start the frontend development server
npm run dev
```

The web application will be accessible at `http://localhost:5173`.

---

## Environment Variables

By default, the backend runs on `localhost:8000` and the frontend expects the backend to be there. 
If needed, create a `.env` file in the `frontend/` directory:
```env
VITE_API_URL=http://localhost:8000
```
And a `.env` file in the root directory for backend configuration overrides:
```env
# Optional overrides
CONFIDENCE_THRESHOLD=0.5
IMAGE_SIZE=640
```

## ML Models

The system expects trained ML model weights to be present in `./ml/weights/`:
- `food_detection.pt` - YOLOv8 model for food detection.
- `portion_model.joblib` - XGBoost model for portion estimation.

*If you are missing these models, ensure you run the training scripts in the `ml/` folder or place the pre-trained weights in the `ml/weights/` directory before starting the backend.*