from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ZOL AI Voice Receptionist Backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
