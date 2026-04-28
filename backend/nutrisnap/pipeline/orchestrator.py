"""Pipeline-level SequentialOrchestrator — re-exports from app.services.orchestrator.

This shim keeps the pipeline package's import path consistent with 02-01-PLAN.md
while the actual implementation lives in app/services/orchestrator.py.
"""

from app.services.orchestrator import (  # noqa: F401
    PipelineResult,
    SequentialOrchestrator,
)

__all__ = ["SequentialOrchestrator", "PipelineResult"]
