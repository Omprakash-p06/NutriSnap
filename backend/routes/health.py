"""Health Check Endpoint.

Provides application health status for monitoring and load balancers.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Check application health status.

    Returns:
        Health status dictionary.
    """
    return {"status": "healthy", "service": "nutrisnap-api"}
