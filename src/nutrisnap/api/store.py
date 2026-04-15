"""Async SQLite store for NutriSnap prediction jobs."""
import json
import logging
import aiosqlite
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from nutrisnap.api.models import JobStatus, PredictionResult, JobResponse

logger = logging.getLogger(__name__)


class ResultStore:
    """Handles persistence of prediction jobs and results."""

    def __init__(self, db_path: str | Path = "data/nutrisnap.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Create tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    result_json TEXT,
                    error TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)
            await db.commit()

    async def create_job(self, job_id: str):
        """Register a new pending job."""
        now = datetime.now(timezone.utc)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO jobs (job_id, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (job_id, JobStatus.PENDING, now, now)
            )
            await db.commit()

    async def update_status(self, job_id: str, status: JobStatus, error: Optional[str] = None):
        """Update job status and optional error message."""
        now = datetime.now(timezone.utc)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE jobs SET status = ?, error = ?, updated_at = ? WHERE job_id = ?",
                (status, error, now, job_id)
            )
            await db.commit()

    async def save_result(self, job_id: str, result: Dict[str, Any]):
        """Save final prediction result and mark as COMPLETED."""
        now = datetime.now(timezone.utc)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE jobs SET status = ?, result_json = ?, updated_at = ? WHERE job_id = ?",
                (JobStatus.COMPLETED, json.dumps(result), now, job_id)
            )
            await db.commit()

    async def get_job(self, job_id: str) -> Optional[JobResponse]:
        """Fetch job details by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)) as cursor:
                row = await cursor.fetchone()
                
                if not row:
                    return None
                    
                result = None
                if row["result_json"]:
                    result_data = json.loads(row["result_json"])
                    result = PredictionResult(**result_data)
                    
                return JobResponse(
                    job_id=row["job_id"],
                    status=JobStatus(row["status"]),
                    created_at=row["created_at"],
                    result=result,
                    error=row["error"]
                )
