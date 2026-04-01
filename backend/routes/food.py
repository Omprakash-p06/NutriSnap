"""Food Analysis Endpoints.

Handles image upload and food detection/nutrition analysis.
"""

import os
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.schemas.food import AnalysisResponse
from backend.services.food_analysis import FoodAnalysisService

router = APIRouter()

# Initialize service
service = FoodAnalysisService()
executor = ThreadPoolExecutor(max_workers=1)


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_food_image(
    file: UploadFile = File(..., description="Food image to analyze")
) -> AnalysisResponse:
    """Analyze food image and return nutrition information.

    This endpoint accepts an image file, runs food detection,
    portion estimation, and nutrition calculation.
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, detail=f"Invalid file type. Allowed: {allowed_types}"
        )

    # Save uploaded file temporarily
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = f"{temp_dir}/{uuid.uuid4()}_{file.filename}"

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Run analysis in threadpool to avoid blocking event loop
        # (AI models are CPU/GPU intensive and blocking)
        import asyncio  # pylint: disable=import-outside-toplevel

        loop = asyncio.get_event_loop()
        image_id = str(uuid.uuid4())
        response = await loop.run_in_executor(
            executor, service.analyze_image, file_path, image_id
        )

        return response

    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        import traceback  # pylint: disable=import-outside-toplevel

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

    finally:
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
