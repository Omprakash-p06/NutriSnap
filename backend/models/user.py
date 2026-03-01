# pylint: disable=too-few-public-methods

"""User SQLAlchemy Model.

Defines the User table for storing user profiles.
"""

from sqlalchemy import Column, Float, Integer, String

from backend.database import Base


class User(Base):
    """User database model.

    Attributes:
        id: Primary key.
        name: User's display name.
        height_cm: Height in centimeters.
        weight_kg: Weight in kilograms.
        age: User's age.
        activity_level: Activity level (sedentary/moderate/active).
        goal: Nutrition goal (lose/maintain/gain).
        daily_target_kcal: Daily calorie target.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, default="Guest User")
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    age = Column(Integer, nullable=True)
    activity_level = Column(String(20), default="moderate")
    goal = Column(String(20), default="maintain")
    daily_target_kcal = Column(Integer, default=2000)
