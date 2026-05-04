"""NutriSnap FastAPI Application — Production-Hardened Entry Point."""

import asyncio
import gc
import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.database import close_mongo_connection, connect_to_mongo
from app.exceptions import register_exception_handlers
from app.middleware import RequestLoggingMiddleware
from app.routers import chat as chat_router
from app.routers import food, insights
from app.routers import health as health_router
from app.routers import logs, planning, prediction, social, users, water
from app.services.mapping import IngredientMappingService
from app.services.orchestrator import SequentialOrchestrator
from app.services.task_manager import cleanup_jobs

# Load environment variables
load_dotenv()

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


async def _periodic_cleanup():
    """Background task to clear memory-leaking prediction jobs."""
    while True:
        try:
            count = cleanup_jobs(max_age_seconds=3600)
            if count > 0:
                logger.info(f"Cleaned up {count} expired prediction jobs from memory")
        except Exception as exc:
            logger.error(f"Cleanup task failed: {exc}")
        await asyncio.sleep(3600)  # Run every hour


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()

    # Start cleanup worker
    cleanup_task = asyncio.create_task(_periodic_cleanup())

    # Initialize IngredientMappingService (always available, no GPU needed)
    app.state.mapping = IngredientMappingService()
    logger.info("IngredientMappingService loaded")

    skip_ai = os.getenv("SKIP_AI_INIT", "false").lower() == "true"

    if skip_ai:
        logger.info("SKIP_AI_INIT=true — using mock orchestrator for CI/testing")
        app.state.orchestrator = SequentialOrchestrator(mock=True)
    else:
        try:
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            app.state.orchestrator = SequentialOrchestrator(device=device)
            logger.info(f"SequentialOrchestrator initialized on {device}")
        except Exception as exc:
            logger.warning(f"GPU init failed, falling back to mock orchestrator: {exc}")
            app.state.orchestrator = SequentialOrchestrator(mock=True)

    logger.info("NutriSnap API started ✅")
    yield

    # Shutdown — release GPU memory
    cleanup_task.cancel()
    if hasattr(app.state, "orchestrator"):
        app.state.orchestrator.teardown()
        del app.state.orchestrator

    # Force GPU cleanup
    try:
        import torch

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("GPU memory released")
    except Exception:
        pass

    await close_mongo_connection()
    logger.info("NutriSnap API shut down 🛑")


# ---------------------------------------------------------------------------
# OpenAPI tags for Swagger grouping
# ---------------------------------------------------------------------------
tags_metadata = [
    {"name": "users", "description": "User profile management."},
    {"name": "food", "description": "USDA food search and nutrition data."},
    {"name": "meal-logs", "description": "Daily meal logging (CRUD)."},
    {
        "name": "planning",
        "description": "Personalized meal planning and daily summaries.",
    },
    {
        "name": "prediction",
        "description": "AI-powered nutrition estimation from meal photos.",
    },
    {"name": "water", "description": "Hydration tracking."},
    {"name": "insights", "description": "AI-powered nutrition insights."},
    {"name": "social", "description": "Community feed and social sharing."},
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
    "http://localhost:3000,http://localhost:5173,https://nutrisnap.vercel.app",
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
app.include_router(users.router)
app.include_router(food.router)
app.include_router(logs.router)
app.include_router(planning.router)
app.include_router(prediction.router)
app.include_router(water.router)
app.include_router(insights.router)
app.include_router(social.router)
app.include_router(health_router.router)
app.include_router(chat_router.router)


@app.get("/", tags=["monitoring"])
async def root():
    """Root endpoint — quick liveness probe."""
    return {"message": "NutriSnap Backend Running 🚀"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=5000, reload=True)
