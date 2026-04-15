"""Pydantic models for the NutriSnap API."""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Refinement(BaseModel):
    """Refined estimation from LLM fallback."""
    calories: float
    fat: float
    carbs: float
    protein: float
    reasoning: str
    confidence: float


class PredictionResult(BaseModel):
    """Nutrition prediction outcome."""
    calories: float
    fat: float
    carbs: float
    protein: float
    
    # Metadata
    is_flagged: bool = False
    verification_reason: Optional[str] = None
    ensemble_variance: Optional[float] = None
    
    # Optional LLM Fallback (VERI-02)
    llm_refinement: Optional[Refinement] = None


class JobResponse(BaseModel):
    """Standard response for a prediction job."""
    job_id: str
    status: JobStatus
    created_at: datetime
    result: Optional[PredictionResult] = None
    error: Optional[str] = None
