"""FastAPI application for NutriSnap Nutrition Estimation."""

import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, UploadFile

from nutrisnap.api.models import JobResponse
from nutrisnap.api.store import ResultStore
from nutrisnap.api.worker import JobWorker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global State
_store: Optional[ResultStore] = None
_worker: Optional[JobWorker] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _store, _worker
    # Initialize global state
    _store = ResultStore()
    await _store.initialize()

    # Ensure data directory exists
    Path("datasets/uploads").mkdir(parents=True, exist_ok=True)

    _worker = JobWorker(_store)

    yield

    # Cleanup
    _store = None
    _worker = None


app = FastAPI(
    title="NutriSnap API",
    description="Estimate nutrition from meal photos using a modular AI pipeline",
    version="0.1.0",
    lifespan=lifespan,
)


def get_store():
    return _store


def get_worker():
    return _worker


@app.get("/")
async def root():
    return {"message": "NutriSnap API is running", "version": "0.1.0"}


@app.post("/predict", response_model=JobResponse)
async def predict(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    store: ResultStore = Depends(get_store),
    worker: JobWorker = Depends(get_worker),
):
    """Submit a meal image for nutrition estimation."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    job_id = str(uuid.uuid4())

    # Save file
    file_ext = Path(file.filename).suffix or ".jpg"
    upload_path = Path("datasets/uploads") / f"{job_id}{file_ext}"

    try:
        content = await file.read()
        with open(upload_path, "wb") as f:
            f.write(content)

        # Create job record
        await store.create_job(job_id)

        # Trigger background worker
        background_tasks.add_task(worker.process_job, job_id, content)

        logger.info(f"Accepted job {job_id}. Image saved to {upload_path}")

    except Exception as e:
        logger.error(f"Failed to ingest job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to persist image")

    return await store.get_job(job_id)


@app.get("/result/{job_id}", response_model=JobResponse)
async def get_result(job_id: str, store: ResultStore = Depends(get_store)):
    """Retrieve the status and results of a prediction job."""
    job = await store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
