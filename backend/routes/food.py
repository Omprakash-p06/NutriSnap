"""Food Analysis Endpoints.

Handles image upload and food detection/nutrition analysis.
"""

import os
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, File, HTTPException, UploadFile

from ai_engine.coordinator import FoodAnalysisCoordinator
from backend.schemas.food import AnalysisResponse, DetectedFood
from backend.schemas.nutrition import NutritionInfo

router = APIRouter()

# Initialize coordinator (lazy loading models)
coordinator = FoodAnalysisCoordinator()
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
        result = await loop.run_in_executor(
            executor, coordinator.analyze_image, file_path
        )

        if not result["success"]:
            raise HTTPException(
                status_code=500, detail=result.get("message", "Analysis failed")
            )

        # Map results to schema
        detected_foods = []
        for item in result["detections"]:
            detected_foods.append(
                DetectedFood(
                    food_class=item["class"],
                    confidence=item["confidence"],
                    bbox=item["bbox"],
                    estimated_grams=item["estimated_grams"],
                    portion_unit=item.get("portion_unit", "g"),
                    portion_amount=item.get("portion_amount", item["estimated_grams"]),
                    portion_display=item.get(
                        "portion_display", f"{int(item['estimated_grams'])}g"
                    ),
                    nutrition=(
                        NutritionInfo(**item["nutrition"])
                        if "nutrition" in item
                        else None
                    ),
                )
            )

        return AnalysisResponse(
            success=True,
            image_id=str(uuid.uuid4()),
            detected_foods=detected_foods,
            total_nutrition=NutritionInfo(**result["total_nutrition"]),
        )

    except Exception as e:
        import traceback  # pylint: disable=import-outside-toplevel

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

    finally:
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
