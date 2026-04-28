"""app/utils/tasks.py — AsyncTaskManager shim.

Re-exports task management functions from app/services/task_manager.py,
satisfying the path expected by 02-02-PLAN.md.
"""

from app.services.task_manager import (  # noqa: F401
    InferenceJob,
    JobStatus,
    create_job,
    get_job,
    update_job,
)

__all__ = ["JobStatus", "InferenceJob", "create_job", "get_job", "update_job"]
