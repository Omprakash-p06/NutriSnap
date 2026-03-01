# pylint: disable=too-few-public-methods

"""FoodItem SQLAlchemy Model.

Defines the FoodItem table for individual detected foods in a meal.
"""

from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.database import Base


class FoodItem(Base):
    """Food item database model.

    Attributes:
        id: Primary key.
        meal_id: Foreign key to meals table.
        food_class: Food class name (rice, dal, paneer, roti).
        confidence: Detection confidence score.
        ai_portion_grams: AI estimated portion in grams.
        user_portion_grams: User corrected portion in grams.
        calories: Calculated calories for this item.
        protein: Calculated protein in grams.
        carbs: Calculated carbohydrates in grams.
        fats: Calculated fats in grams.
    """

    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id"), nullable=False)
    food_class = Column(String(50), nullable=False)
    confidence = Column(Float, default=0.0)
    ai_portion_grams = Column(Float, nullable=False)
    user_portion_grams = Column(Float, nullable=False)
    calories = Column(Float, nullable=False, default=0.0)
    protein = Column(Float, nullable=False, default=0.0)
    carbs = Column(Float, nullable=False, default=0.0)
    fats = Column(Float, nullable=False, default=0.0)

    # Relationships
    meal = relationship("Meal", back_populates="food_items")
