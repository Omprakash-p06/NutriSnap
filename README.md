# NutriSnap 🍱

**AI-powered nutrition companion for personalized fitness and healthy living.**

NutriSnap is a comprehensive nutrition tracking platform that uses an advanced AI ensemble to estimate calories and macros from a single photo. It combines state-of-the-art computer vision with a personalized user experience, featuring offline-first logging, interactive progress dashboards, and an intelligent meal planner.

---

## 🏗️ Architecture & AI Pipeline

![NutriSnap Architecture](docs/architecture.svg)

NutriSnap employs a **three-tier, 3D-aware pipeline** to ensure high-accuracy detection and mass estimation even for rare food items or difficult lighting.

### 🧠 The Three-Tier Detection Strategy

1.  **Tier 1: OWL-ViT Zero-Shot Primary** — Our primary detector uses Google's OWL-ViT zero-shot detector on overlapping tiles with a low confidence threshold (0.05). This ensures extremely high recall, successfully catching rare dishes, small ingredients, or food under unusual lighting.
2.  **Tier 2: YOLOv8 Secondary Supplement** — A secondary pass uses YOLOv8 to supplement the detections by catching common dishes with high confidence (> 0.5) that do not overlap with OWL-ViT detections.
3.  **Tier 3: LLM Validation & Realism Check** — All detections are filtered through a Gemini-powered validator to remove non-food items (furniture, pets) and ensure nutritional estimates are physically plausible.

### 🔬 High-Resolution Optimizations

-   **Enhanced Preprocessing**: Every image undergoes automated sharpening and **CLAHE (Contrast Limited Adaptive Histogram Equalization)** to recover texture details from mobile photos.
-   **Tiled Inference**: For high-resolution uploads, the system uses an overlapping tile strategy for Zero-Shot detection, ensuring small food items (like peas in a pulao) are not missed due to downscaling.
-   **Volumetric Reconstruction**: Combines **SAM 2** (Segmentation) and **GLPN** (Depth Estimation) to recover 3D volume from a single 2D photo.

---

## ✨ Key Features

-   **📸 AI Food Scanning**: Real-time nutrition estimation (Calories, Protein, Carbs, Fat) from a single meal photo.
-   **📊 Progress Dashboard**: Interactive visualizations of your 7-day intake and macro distribution using Recharts.
-   **🥗 Meal Planner**: A rule-based engine that suggests personalized recipes based on your real-time nutritional gaps.
-   **🔌 Offline-First (PWA)**: Built with Dexie.js for IndexedDB storage, ensuring the app works perfectly without an internet connection.
-   **🔒 Secure Auth**: JWT-based authentication with Guest User fallback.

---

## 🛠️ Tech Stack

### Backend
-   **Framework**: FastAPI (Python)
-   **AI Engines**: PyTorch, Transformers (SAM 2, GLPN, OWL-ViT), Ultralytics (YOLOv8)
-   **Database**: SQLite (Zero-config, Local Persistence)
-   **Logging**: Loguru

### Frontend
-   **Framework**: React (Vite)
-   **State & Offline**: Dexie.js (IndexedDB)
-   **Charts**: Recharts
-   **Animations**: Framer Motion
-   **Icons**: Lucide React

---

## 🚀 Getting Started

### 1. Prerequisites
-   Node.js 20+
-   Python 3.11+
-   CUDA 12.x (Highly Recommended for AI inference, but CPU is supported)

### 2. Clone and Install Dependencies

```powershell
git clone https://github.com/yourusername/NutriSnap.git
cd NutriSnap

# Setup Backend
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Setup Frontend
cd ../frontend
npm install
cd ..
```

### 3. Download AI Model Weights (~1 GB)

NutriSnap relies on several large pre-trained models. To make collaboration easy, we use a setup script that pre-fetches all weights to your local Hugging Face and Ultralytics caches. **You only need to run this once.**

```powershell
# From the backend directory with venv activated:
python scripts/download_models.py
```

### 4. Environment Variables & Credentials
**⚠️ Security Warning**: Never commit your `.env` files to version control.

1. **Backend**: Copy `.env.example` to `.env` in the `backend/` directory:
   ```powershell
   cd backend
   cp .env.example .env
   ```
   Open `backend/.env` and configure:
   - `SECRET_KEY`: Set to a secure random string.
   - `GEMINI_API_KEY`: Required for LLM validation. Get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey).
   - `SKIP_AI_INIT`: Set to `false` to enable real AI inference. Set to `true` if you only want to work on frontend/API without loading heavy ML models.

2. **Frontend**: Create a `.env` file in the `frontend/` directory:
   ```env
   VITE_API_URL=http://localhost:5000
   ```

### 5. Start the Services

The easiest way to start both the frontend and backend simultaneously is to use the `start.py` script in the root directory.

```powershell
# Run from the project root
python start.py
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

*(If you prefer manual startup, run `uvicorn app.main:app --reload --port 5000` in the backend and `npm run dev` in the frontend).*

### 🐳 6. Docker Fallback (Foolproof Setup)

If you have trouble installing Python/Node or configuring environments on your machine, you can run the entire stack using Docker. We have configured a **Development Container Setup** with live-reloading.

```powershell
# 1. Download models first (this is still required locally so Docker can mount them)
python backend/scripts/download_models.py

# 2. Start the entire application
docker-compose up --build
```
- **Live Edit**: You can edit the code in `frontend/` or `backend/` and the Docker containers will automatically restart/hot-reload.
- **GPU Acceleration**: Open `docker-compose.yml` and uncomment the `deploy: resources: ...` section under the backend service if you want to use an NVIDIA GPU inside Docker.

---

## 🔌 API Overview

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| **Auth** | | |
| `/auth/signup` | POST | Register a new user and return JWT. |
| `/auth/login` | POST | Authenticate user and return JWT. |
| `/auth/guest` | GET | Authenticate guest user and return guest JWT. |
| **Scan (Predict)** | | |
| `/predict/` | POST | Upload an image for AI nutrition estimation. Returns job ID. |
| `/predict/status/{id}` | GET | Poll prediction job status. |
| `/predict/validated` | POST | Confirm and save validated prediction results. |
| **Meals** | | |
| `/logs/` | POST | Log a new meal entry. |
| `/logs/` | GET | Retrieve user's logged meals list. |
| `/logs/{id}` | DELETE | Delete a specific meal log. |
| `/logs/weekly` | GET | Get weekly logged meals summary. |
| **Water (Hydration)** | | |
| `/water/` | POST | Log new water intake. |
| `/water/today` | GET | Retrieve today's total water intake. |
| `/water/today/logs` | GET | Retrieve today's detailed water logs. |
| `/water/{id}` | DELETE | Delete a specific water log. |
| **Planning** | | |
| `/planning/daily-summary` | GET | Get today's calorie and macro summary. |
| `/planning/weekly-summary` | GET | Get weekly calorie and macro summary. |
| `/planning/suggest` | POST | Suggest personalized recipes based on nutrient gaps. |
| `/planning/recipe-details/{meal_id}` | GET | Get detailed directions for a recipe. |
| **Insights** | | |
| `/insights/` | GET | Retrieve data-driven personalized coaching insights. |
| **Social** | | |
| `/social/posts` | GET/POST | Retrieve or create community/social posts. |
| **Chat** | | |
| `/ws/chat` | WebSocket | Real-time chat with the AI nutrition assistant. |

---

## 🧪 Testing & Diagnostics

### Automated Tests
To run the automated backend test suite, navigate to the `backend` folder and run `pytest`:
```powershell
cd backend
.\venv\Scripts\pytest
```

### Manual & Debugging Scripts
For local debugging, isolated component testing, or reproducing issues, we maintain a collection of standalone scripts in [backend/tests/manual/](file:///c:/Users/OM%20Prakash/Documents/NutriSnap/backend/tests/manual/):
- **API Tests**: `test_api.py` and `reproduce_search.py`
- **Inference Pipeline**: `test_inference.py`
- **WebSocket Chat**: `test_ws.py`
- **Dependency Checks**: `test_dll_deps.py`, `test_current_state.py`, `test_llama_import.py`, `test_minimal_deps.py`

See the [manual tests README](file:///c:/Users/OM%20Prakash/Documents/NutriSnap/backend/tests/manual/README.md) for detailed execution instructions.

---

## 🌍 Deployment Guides

### Backend (Render / Railway)
The backend is Docker-ready.
1. Deploy as a web service with the Root Directory set to `backend`. 
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add all environment variables from `.env`. Ensure your instance has at least 4GB of RAM (or a GPU).

### Frontend (Vercel)
1. Import into Vercel and set the Framework Preset to **Vite**.
2. Root Directory: `frontend`.
3. Add the `VITE_API_URL` environment variable pointing to your deployed backend URL.

---

## 📄 License
MIT — see [LICENSE](LICENSE) for details.
