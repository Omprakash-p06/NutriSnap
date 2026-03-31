"""User Profile Schemas.

Pydantic models for user profile request/response.
"""

from typing import Optional

from pydantic import BaseModel, Field


class UserProfileBase(BaseModel):
    """Base user profile fields.

    All fields are optional to support partial updates.
    """

    name: Optional[str] = Field(None, description="User display name")
    height_cm: Optional[float] = Field(None, description="Height in centimeters")
    weight_kg: Optional[float] = Field(None, description="Weight in kilograms")
    age: Optional[int] = Field(None, description="User age")
    activity_level: Optional[str] = Field(
        None, description="Activity level (sedentary/moderate/active)"
    )
    goal: Optional[str] = Field(
        None, description="Nutrition goal (lose/maintain/gain)"
    )


class UserProfileUpdate(UserProfileBase):
    """Schema for updating a user profile."""

    pass


class UserProfileResponse(UserProfileBase):
    """Full user profile response including computed fields."""

    id: int
    bmi: Optional[float] = Field(None, description="Body Mass Index")
    daily_target_kcal: int = Field(2000, description="Daily calorie target")
    daily_target_protein_g: float = Field(
        150.0, description="Daily protein target in grams"
    )
    daily_target_carbs_g: float = Field(
        200.0, description="Daily carbs target in grams"
    )
    daily_target_fats_g: float = Field(
        65.0, description="Daily fats target in grams"
    )

    class Config:
        """Pydantic config for ORM mode."""

        from_attributes = True
