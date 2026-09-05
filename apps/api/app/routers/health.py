"""Health check endpoints."""
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "prodway-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
