# NutriSnap 🍱

**AI-powered nutrition companion for personalized fitness and healthy living.**

NutriSnap is a comprehensive nutrition tracking platform that uses an advanced AI ensemble to estimate calories and macros from a single photo. It combines state-of-the-art computer vision with a personalized user experience, featuring offline-first logging, interactive progress dashboards, and an intelligent meal planner.

---

## 🏗️ Architecture & AI Pipeline

NutriSnap employs a three-stage, 3D-aware pipeline to recover volumetric information from 2D photos, ensuring high-accuracy mass estimation.

1.  **Segmentation (SAM 2)**: Isolates the food item from its background.
2.  **Depth Estimation (GLPN)**: Generates a depth map to capture 3D structure.
3.  **Nutrition Regression (EfficientNetV2-B0)**: Analyzes a composite of the RGB image, mask, and depth map, fused with explicit volume scalars to predict mass and nutritional content.
4.  **Isotonic Calibration**: A post-inference correction layer that significantly reduces prediction bias.

---

## ✨ Key Features

-   **📸 AI Food Scanning**: Real-time nutrition estimation (Calories, Protein, Carbs, Fat) from a single meal photo.
-   **📊 Progress Dashboard**: Interactive visualizations of your 7-day intake and macro distribution using Recharts.
-   **🥗 Meal Planner**: A rule-based engine that suggests personalized recipes based on your real-time nutritional gaps.
-   **🔌 Offline-First (PWA)**: Built with Dexie.js for IndexedDB storage, ensuring the app works perfectly without an internet connection.
-   **🔒 Secure Auth**: JWT-based authentication with Google OAuth integration.

---

## 🛠️ Tech Stack

### Backend
-   **Framework**: FastAPI (Python)
-   **AI Engines**: PyTorch, Transformers (SAM 2, GLPN), EfficientNetV2
-   **Database**: MongoDB (Cloud Sync)
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
-   Node.js 18+
-   Python 3.10+
-   CUDA 11.8+ (Recommended for AI inference)
-   MongoDB Atlas account or local MongoDB instance

### 2. Environment Variables & Credentials
**⚠️ Security Warning**: Never commit your `.env` files to version control.

1. **Backend**: Create a `.env` file in the `backend/` directory:
   ```env
   # Database
   MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/nutrisnap?retryWrites=true&w=majority
   
   # Security
   JWT_SECRET_KEY=your_super_secret_key_here
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # API Keys (if using external providers for Chatbot)
   OPENAI_API_KEY=sk-...
   ```

2. **Frontend**: Create a `.env` file in the `frontend/` directory (if needed for API URLs):
   ```env
   VITE_API_URL=http://localhost:5000
   ```

### 3. Backend Setup
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 5000
```
*Note: The backend must run on **port 5000** to match the frontend proxy.*

### 4. Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🔌 API Overview

The NutriSnap backend exposes a comprehensive RESTful API:

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| **Auth** |
| `/auth/register` | POST | Register a new user and return JWT. |
| `/auth/login` | POST | Authenticate user and return JWT. |
| **Scan** |
| `/scan/upload` | POST | Upload an image for AI nutrition estimation. Returns task ID. |
| `/scan/status/{id}` | GET | Poll task status and retrieve final prediction. |
| **Meals & Water** |
| `/meals` | POST/GET | Log manual meal entries and retrieve daily history. |
| `/water` | POST/GET | Increment daily water tracking count. |
| **Community** |
| `/community/posts` | GET/POST | Fetch feed or publish a new meal post. |
| `/community/posts/{id}/like` | POST | Like a community post. |
| **Insights** |
| `/insights/weekly` | GET | Retrieve aggregated weekly calorie and macro trends. |
| **Chat** |
| `/chat/message` | POST | Send a message to the AI nutrition assistant (Rate limited). |

---

## 🌍 Deployment Guides

### Backend (Render / Railway)
The backend is Docker-ready and can be easily deployed to container-hosting platforms.
1. **Render**: Create a new "Web Service", connect your repository, and set the Root Directory to `backend`. 
2. Set the Build Command to `pip install -r requirements.txt` and Start Command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Add all variables from your `.env` file into the platform's Environment Variables section.

### Frontend (Vercel)
The Vite frontend is optimized for edge deployment.
1. Import your project into Vercel.
2. Set the Framework Preset to **Vite**.
3. Configure the Root Directory to `frontend`.
4. Add the `VITE_API_URL` environment variable pointing to your deployed backend URL.
5. Deploy!

---

## 📄 License
MIT — see [LICENSE](LICENSE) for details.
