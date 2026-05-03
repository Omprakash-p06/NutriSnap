"""AsyncTaskManager: background inference job tracking.

Stores job state in an in-memory dict (for simplicity). In production,
swap for a Redis backend or MongoDB collection.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


@dataclass
class InferenceJob:
    job_id: str
    user_id: str
    created_at: datetime
    status: JobStatus = JobStatus.QUEUED
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    persisted: bool = False


_jobs: dict[str, InferenceJob] = {}


def create_job(user_id: str) -> InferenceJob:
    job_id = str(uuid.uuid4())
    job = InferenceJob(
        job_id=job_id, user_id=user_id, created_at=datetime.now(timezone.utc)
    )
    _jobs[job_id] = job
    return job


def get_job(job_id: str) -> Optional[InferenceJob]:
    return _jobs.get(job_id)


def update_job(
    job_id: str, status: JobStatus, result: dict | None = None, error: str | None = None
) -> None:
    job = _jobs.get(job_id)
    if job:
        job.status = status
        if result is not None:
            job.result = result
        if error is not None:
            job.error = error


def cleanup_jobs(max_age_seconds: int = 3600) -> int:
    """Remove jobs older than max_age_seconds. Returns number of removed jobs."""
    now = datetime.now(timezone.utc)
    to_remove = [
        job_id
        for job_id, job in _jobs.items()
        if (now - job.created_at).total_seconds() > max_age_seconds
    ]
    for job_id in to_remove:
        del _jobs[job_id]
    return len(to_remove)
