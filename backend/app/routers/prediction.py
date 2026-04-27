from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from datetime import datetime, timezone
import shutil
import os
import tempfile
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.database import get_database
from app.schemas import PredictionOut, MultiFoodPredictionOut, ValidationSummary, PredictedItem
from app.auth import get_current_user

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/predict",
    tags=["prediction"]
)

@router.post("/", response_model=PredictionOut)
@limiter.limit("100/minute")
async def predict_meal(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    # Verify file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save to temp file for processing
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        
    try:
        # Get predictor from app state (initialized in main.py lifespan)
        predictor = request.app.state.predictor
        
        # Run inference
        results = predictor.predict_mass(tmp_path)
        
        # Save to MongoDB
        db = await get_database()
        prediction_doc = {
            "user_id": str(current_user["_id"]),
            "mass_g": results["mass_g"],
            "calories": results["calories"],
            "fat_g": results["fat_g"],
            "carbs_g": results["carbs_g"],
            "protein_g": results["protein_g"],
            "timestamp": datetime.now(timezone.utc)
        }
        
        insert_result = await db.predictions.insert_one(prediction_doc)
        prediction_doc["_id"] = str(insert_result.inserted_id)
        
        return prediction_doc
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")
    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/validated", response_model=MultiFoodPredictionOut)
@limiter.limit("50/minute")
async def predict_validated(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Multi-food detection with LLM validation.
    
    Returns itemized calorie/macro estimates with LLM reasoning.
    Pipeline: YOLOv8 -> SAM 2 -> GLPN -> MultiFoodMerger -> LLMValidator
    
    Latency target: <3s with LLM overhead.
    """
    # Verify file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save to temp file for processing
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    
    try:
        # Get multi-food pipeline from app state
        pipeline = request.app.state.multi_food_pipeline
        
        # Run inference
        result = pipeline.predict(tmp_path)
        
        # Convert to dict for MongoDB
        result_dict = result.to_dict()
        
        # Convert items to Pydantic models
        items = [
            PredictedItem(
                label=item["label"],
                confidence=item["confidence"],
                volume_cm3=item["volume_cm3"],
                mass_g=item["mass_g"],
                calories=item["calories"],
                protein=item["protein"],
                carbs=item["carbs"],
                fat=item["fat"],
            )
            for item in result_dict["items"]
        ]
        
        # Build validation summary
        vs = result_dict["validation_summary"]
        validation_summary = ValidationSummary(
            is_valid=vs["is_valid"],
            reasoning=vs["reasoning"],
            llm_reasoning=vs.get("llm_reasoning") or vs["reasoning"],
            corrections=vs["corrections"],
        )
        
        # Save to MongoDB
        db = await get_database()
        prediction_doc = {
            "user_id": str(current_user["_id"]),
            "items": result_dict["items"],
            "total_calories": result_dict["total_calories"],
            "total_mass_g": result_dict["total_mass_g"],
            "total_protein": result_dict["total_protein"],
            "total_carbs": result_dict["total_carbs"],
            "total_fat": result_dict["total_fat"],
            "validation_summary": vs,
            "latency_seconds": result_dict["latency_seconds"],
            "item_count": result_dict["item_count"],
            "timestamp": datetime.now(timezone.utc)
        }
        
        insert_result = await db.predictions.insert_one(prediction_doc)
        prediction_doc["_id"] = str(insert_result.inserted_id)
        prediction_doc["user_id"] = str(current_user["_id"])
        
        # Return formatted response (mongo _id needs to be at top level)
        response = {
            "_id": prediction_doc["_id"],
            "user_id": str(current_user["_id"]),
            "items": items,
            "total_calories": result_dict["total_calories"],
            "total_mass_g": result_dict["total_mass_g"],
            "total_protein": result_dict["total_protein"],
            "total_carbs": result_dict["total_carbs"],
            "total_fat": result_dict["total_fat"],
            "validation_summary": validation_summary,
            "latency_seconds": result_dict["latency_seconds"],
            "item_count": result_dict["item_count"],
            "timestamp": datetime.now(timezone.utc),
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")
    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
