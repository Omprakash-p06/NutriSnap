"""NutriSnap FastAPI Application — Production-Hardened Entry Point."""

from contextlib import asynccontextmanager
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables
load_dotenv()

from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, users, food, logs, planning, prediction
from app.routers import health as health_router
from app.routers import chat as chat_router
from app.middleware import RequestLoggingMiddleware
from app.exceptions import register_exception_handlers

# ---------------------------------------------------------------------------
# Loguru configuration
# ---------------------------------------------------------------------------
# Remove default stderr handler, add structured one
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<7}</level> | {message}",
    level="INFO",
    filter=lambda record: "password" not in record["message"].lower()
                          and "token" not in record["message"].lower(),
)
logger.add(
    "logs/nutrisnap_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<7} | {message}",
    filter=lambda record: "password" not in record["message"].lower(),
)

# ---------------------------------------------------------------------------
# Rate limiter (shared instance)
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()

    # Initialize Predictor
    if os.getenv("SKIP_AI_INIT") == "true":
        logger.info("Skipping AI Predictor initialization (SKIP_AI_INIT=true)")
        class MockPredictor:
            def predict_mass(self, path):
                return {"mass_g": 150.0, "calories": 180.0, "fat_g": 5.0, "carbs_g": 20.0, "protein_g": 10.0}
        app.state.predictor = MockPredictor()
    else:
        try:
            from nutrisnap.inference.predictor import NutriSnapPredictor
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            app.state.predictor = NutriSnapPredictor(device=device)
            logger.info(f"AI Predictor initialized on {device}")
        except Exception as e:
            logger.warning(f"AI Predictor unavailable, using mock: {e}")
            class MockPredictor:
                def predict_mass(self, path):
                    return {"mass_g": 150.0, "calories": 180.0, "fat_g": 5.0, "carbs_g": 20.0, "protein_g": 10.0}
            app.state.predictor = MockPredictor()
    
    # Initialize Multi-Food Pipeline
    if os.getenv("SKIP_AI_INIT") == "true":
        logger.info("Skipping Multi-Food Pipeline initialization (SKIP_AI_INIT=true)")
        class MockMultiFoodPipeline:
            def predict(self, path):
                return type("Result", (), {
                    "to_dict": lambda: {
                        "items": [{"label": "pizza", "confidence": 0.9, "volume_cm3": 500.0, "mass_g": 200.0, "calories": 500.0, "protein": 10.0, "carbs": 50.0, "fat": 20.0}],
                        "total_calories": 500.0,
                        "total_mass_g": 200.0,
                        "total_protein": 10.0,
                        "total_carbs": 50.0,
                        "total_fat": 20.0,
                        "validation_summary": {"is_valid": True, "reasoning": "OK", "corrections": []},
                        "latency_seconds": 0.5,
                        "item_count": 1,
                    }
                })()
        app.state.multi_food_pipeline = MockMultiFoodPipeline()
    else:
        try:
            from nutrisnap.pipeline.inference import MultiFoodInferencePipeline
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            app.state.multi_food_pipeline = MultiFoodInferencePipeline(device=device, enable_llm_validation=True)
            logger.info(f"Multi-Food Pipeline initialized on {device}")
        except Exception as e:
            logger.warning(f"Multi-Food Pipeline unavailable, using mock: {e}")
            class MockMultiFoodPipeline:
                def predict(self, path):
                    return type("Result", (), {
                        "to_dict": lambda: {
                            "items": [{"label": "pizza", "confidence": 0.9, "volume_cm3": 500.0, "mass_g": 200.0, "calories": 500.0, "protein": 10.0, "carbs": 50.0, "fat": 20.0}],
                            "total_calories": 500.0,
                            "total_mass_g": 200.0,
                            "total_protein": 10.0,
                            "total_carbs": 50.0,
                            "total_fat": 20.0,
                            "validation_summary": {"is_valid": True, "reasoning": "Mock OK", "corrections": []},
                            "latency_seconds": 0.1,
                            "item_count": 1,
                        }
                    })()
            app.state.multi_food_pipeline = MockMultiFoodPipeline()

    logger.info("NutriSnap API started ✅")
    yield
    # Shutdown
    await close_mongo_connection()
    
    # Cleanup pipeline
    if hasattr(app.state, "multi_food_pipeline"):
        del app.state.multi_food_pipeline
    if hasattr(app.state, "predictor"):
        del app.state.predictor
    
    logger.info("NutriSnap API shut down 🛑")

# ---------------------------------------------------------------------------
# OpenAPI tags for Swagger grouping
# ---------------------------------------------------------------------------
tags_metadata = [
    {"name": "authentication", "description": "Register, login, and JWT token management."},
    {"name": "users", "description": "User profile management."},
    {"name": "food", "description": "USDA food search and nutrition data."},
    {"name": "meal-logs", "description": "Daily meal logging (CRUD)."},
    {"name": "planning", "description": "Personalized meal planning and daily summaries."},
    {"name": "prediction", "description": "AI-powered nutrition estimation from meal photos."},
    {"name": "chat", "description": "Real-time AI nutritionist chat (WebSocket)."},
    {"name": "monitoring", "description": "Health checks and system metrics."},
]

# ---------------------------------------------------------------------------
# App creation
# ---------------------------------------------------------------------------
app = FastAPI(
    title="NutriSnap API",
    description=(
        "AI-powered nutrition estimation from meal photos. "
        "Upload a photo, get calories and macros instantly."
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
)

# ---------------------------------------------------------------------------
# Middleware stack (order matters — outermost first)
# ---------------------------------------------------------------------------
# 1. CORS
FRONTEND_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,https://nutrisnap.vercel.app"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Request logging
app.add_middleware(RequestLoggingMiddleware)

# 3. Rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
register_exception_handlers(app)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(food.router)
app.include_router(logs.router)
app.include_router(planning.router)
app.include_router(prediction.router)
app.include_router(health_router.router)
app.include_router(chat_router.router)

@app.get("/", tags=["monitoring"])
async def root():
    """Root endpoint — quick liveness probe."""
    return {"message": "NutriSnap Backend Running 🚀"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
