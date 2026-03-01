"""FastAPI Application Entry Point.

This module creates and configures the FastAPI application instance.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import create_tables
from backend.routes import dashboard, food, health, meals


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Creates database tables on startup.

    Args:
        _app: FastAPI application instance (unused).

    Yields:
        None
    """
    # Startup: Create database tables
    create_tables()
    yield
    # Shutdown: Cleanup if needed


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app_instance = FastAPI(
        title="NutriSnap AI",
        description="Ingredient-Aware Multi-Food Detection and Nutrition Estimation",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app_instance.include_router(health.router, tags=["Health"])
    app_instance.include_router(food.router, prefix="/api/v1", tags=["Food Analysis"])
    app_instance.include_router(meals.router, prefix="/api/v1", tags=["Meals"])
    app_instance.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])

    return app_instance


app = create_app()
