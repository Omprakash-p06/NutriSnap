# NutriSnap Frontend 🥗

NutriSnap is an AI-powered fitness and nutrition tracking application. This frontend is built with React and Vite, featuring a glassmorphic design and direct integration with a production-ready ML pipeline.

## 🚀 Key Features

- **AI Food Scanning**: Uses SAM2 and EfficientNet models (via Python backend) to estimate food mass and nutrition from a single photo.
- **Smart Logging**: Manual search and voice-controlled logging.
- **Health Dashboard**: Real-time tracking of calories, macros, and hydration.
- **Community Feed**: Share your healthy meals with the Snap Circle.
- **AI Assistant**: Real-time chat with a nutrition coach powered by Gemini 2.0.

## 🛠️ Setup & Installation

### Prerequisites

- Node.js 18+
- Python Backend running on `http://localhost:8000`

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env` file (optional, defaults are provided):
   ```env
   VITE_API_URL=http://localhost:8000
   ```

### Running in Development

```bash
npm run dev
```

The app will be available at `http://localhost:5173`. API calls are proxied to the backend automatically via `vite.config.js`.

## 📡 API Integration

The frontend communicates with a Python FastAPI backend.

- **Authentication**: JWT-based (login/signup).
- **Inference**: Asynchronous polling for image analysis results.
- **Proxy**: `/api/*` requests are forwarded to the backend.

## 📁 Project Structure

- `src/context/AuthContext.jsx`: Global authentication and user settings state.
- `src/services/api.js`: Centralized API service for backend communication.
- `src/hooks/usePrediction.js`: Custom hook for polling the ML inference pipeline.
- `src/pages/Home.jsx`: Main entry point with dashboard and scanner.

## 🧪 Deployment

- **Frontend**: Recommended to deploy on Vercel or Netlify.
- **Backend**: Requires a GPU-enabled environment (e.g., Lambda Labs, Paperspace, or local server).
- Ensure `VITE_API_URL` is correctly set in your CI/CD environment.

## 📜 License

MIT
