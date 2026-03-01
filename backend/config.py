# pylint: disable=too-few-public-methods

"""Application Configuration Settings.

This module defines configuration settings using Pydantic BaseSettings
for environment variable management.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        app_name: Application name.
        env: Environment (development/production).
        debug: Debug mode flag.
        database_url: SQLite database URL.
        model_path: Path to ML model weights.
        cors_origins: Allowed CORS origins.
        confidence_threshold: Minimum detection confidence.
        default_daily_target: Default daily calorie target.
    """

    app_name: str = "NutriSnap AI"
    env: str = "development"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./data/nutrisnap.db"

    # Model paths
    model_path: str = "./ml/weights/"
    yolo_model_name: str = "food_detection.pt"
    portion_model_name: str = "portion_model.joblib"

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Detection settings
    confidence_threshold: float = 0.5
    image_size: int = 640

    # Nutrition defaults
    default_daily_target: int = 2000

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings instance.
    """
    return Settings()


settings = get_settings()
