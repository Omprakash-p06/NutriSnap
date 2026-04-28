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

### 2. Backend Setup
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 5000
```
*Note: The backend must run on **port 5000** to match the frontend proxy.*

### 3. Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 📄 License
MIT — see [LICENSE](LICENSE) for details.
