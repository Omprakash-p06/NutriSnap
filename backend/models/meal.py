# pylint: disable=too-few-public-methods

"""Meal SQLAlchemy Model.

Defines the Meal table for storing logged meals.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.database import Base


class Meal(Base):
    """Meal database model.

    Attributes:
        id: Primary key.
        user_id: Foreign key to users table.
        image_url: Path or URL to meal image.
        total_calories: Total meal calories.
        total_protein: Total protein in grams.
        total_carbs: Total carbohydrates in grams.
        total_fats: Total fats in grams.
        logged_at: Timestamp when meal was logged.
        food_items: Relationship to food items in this meal.
    """

    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)
    image_url = Column(String(500), nullable=True)
    total_calories = Column(Float, nullable=False, default=0.0)
    total_protein = Column(Float, nullable=False, default=0.0)
    total_carbs = Column(Float, nullable=False, default=0.0)
    total_fats = Column(Float, nullable=False, default=0.0)
    logged_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    food_items = relationship(
        "FoodItem",
        back_populates="meal",
        cascade="all, delete-orphan",
    )
