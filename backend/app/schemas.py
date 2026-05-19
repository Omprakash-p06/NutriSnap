from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


class Goal(str, Enum):
    WEIGHT_LOSS = "weight_loss"
    MAINTENANCE = "maintenance"
    MUSCLE_GAIN = "muscle_gain"


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    gender: Optional[Gender] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    age: Optional[int] = None
    activity_level: Optional[ActivityLevel] = None
    goal: Optional[Goal] = None
    location: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    gender: Optional[Gender] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    age: Optional[int] = None
    activity_level: Optional[ActivityLevel] = None
    goal: Optional[Goal] = None
    settings: Optional[dict] = None
    location: Optional[str] = None


class UserOut(BaseModel):
    id: Optional[int] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    gender: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    age: Optional[int] = None
    activity_level: Optional[str] = None
    goal: Optional[str] = None
    xp: int = 0
    level: int = 1
    settings: Optional[dict] = None
    location: Optional[str] = None

    model_config = {"populate_by_name": True, "from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class MealLogBase(BaseModel):
    food_name: str
    calories: float
    protein: float
    carbs: float
    fat: float
    mass_g: Optional[float] = None
    category: Optional[str] = None
    logged_at: Optional[datetime] = None


class MealLogCreate(MealLogBase):
    pass


class MealLogOut(MealLogBase):
    id: Optional[int] = None
    user_email: Optional[str] = None
    timestamp: Optional[str] = None

    model_config = {"populate_by_name": True, "from_attributes": True}


class PredictionOut(BaseModel):
    id: str = Field(..., validation_alias="_id")
    user_id: str
    mass_g: float
    calories: float
    fat_g: float
    carbs_g: float
    protein_g: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True, "from_attributes": True}


# Multi-food validated prediction schemas


class ValidationSummary(BaseModel):
    """LLM validation summary."""

    is_valid: bool
    reasoning: str
    llm_reasoning: Optional[str] = None
    corrections: List[dict] = Field(default_factory=list)


class PredictedItem(BaseModel):
    """Single predicted food item."""

    label: str
    confidence: float
    volume_cm3: float
    mass_g: float
    calories: float
    protein: float
    carbs: float
    fat: float


class MultiFoodPredictionOut(BaseModel):
    """Response for /predict/validated endpoint."""

    id: str = Field(..., validation_alias="_id")
    user_id: str
    items: List[PredictedItem]
    total_calories: float
    total_mass_g: float
    total_protein: float
    total_carbs: float
    total_fat: float
    validation_summary: ValidationSummary
    latency_seconds: float
    item_count: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True, "from_attributes": True}


class WaterLogCreate(BaseModel):
    amount: int  # amount in ml


class WaterLogOut(WaterLogCreate):
    id: Optional[int] = None
    user_email: Optional[str] = None
    timestamp: Optional[str] = None

    model_config = {"populate_by_name": True, "from_attributes": True}


class InsightOut(BaseModel):
    title: str
    message: str
    type: str


class PostCreate(BaseModel):
    userName: str
    mealName: str
    calories: float
    imageUrl: Optional[str] = None


class PostOut(PostCreate):
    id: str = Field(..., validation_alias="_id")
    user_id: str
    likes: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True, "from_attributes": True}
