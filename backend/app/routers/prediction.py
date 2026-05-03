"""Prediction router: async multi-food inference with background task polling."""

from __future__ import annotations

import os
import shutil
import tempfile
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth import get_current_user
from app.database import get_database
from app.services.task_manager import (
    JobStatus,
    cleanup_jobs,
    create_job,
    get_job,
    update_job,
)

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/predict", tags=["prediction"])


# ─────────────────────────────────────────────────────────────────────────────
# Background worker
# ─────────────────────────────────────────────────────────────────────────────


def _run_inference(job_id: str, image_path: str, request: Request) -> None:
    """Synchronous background task — runs in a thread pool via FastAPI."""
    try:
        update_job(job_id, JobStatus.PROCESSING)
        orchestrator = request.app.state.orchestrator
        mapping = request.app.state.mapping

        result = orchestrator.predict(image_path)
        result_dict = result.to_dict()

        # Enrich items with ingredient breakdown
        result_dict["items"] = mapping.enrich(result_dict["items"])

        update_job(job_id, JobStatus.DONE, result=result_dict)
    except Exception as exc:
        update_job(job_id, JobStatus.FAILED, error=str(exc))
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/", response_model=dict)
@limiter.limit("30/minute")
async def submit_prediction(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Submit an image for multi-food inference (async).

    Returns a ``job_id`` immediately. Poll ``/predict/status/{job_id}``
    to retrieve the result when processing completes.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, detail="File must be an image (jpg/png/webp)."
        )

    # Persist to temp file — the background task deletes it after inference
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    job = create_job(user_id=str(current_user["_id"]))
    background_tasks.add_task(_run_inference, job.job_id, tmp_path, request)
    background_tasks.add_task(cleanup_jobs)

    return {"job_id": job.job_id, "status": job.status}


@router.get("/status/{job_id}", response_model=dict)
async def get_prediction_status(
    job_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Poll inference job status.

    Returns status (queued/processing/done/failed) and the full result when done.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.user_id != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized.")

    payload: dict = {"job_id": job_id, "status": job.status}
    if job.status == JobStatus.DONE and job.result:
        payload["result"] = job.result
        # Persist to MongoDB once
        if not job.persisted:
            db = await get_database()
            doc = {
                **job.result,
                "user_id": str(current_user["_id"]),
                "timestamp": datetime.now(timezone.utc),
            }
            await db.predictions.insert_one(doc)
            job.persisted = True
    elif job.status == JobStatus.FAILED:
        payload["error"] = job.error

    return payload


@router.post("/validated", response_model=dict)
@limiter.limit("20/minute")
async def submit_validated_prediction(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Alias of ``/predict/`` — provided for API compatibility."""
    return await submit_prediction(request, background_tasks, file, current_user)
