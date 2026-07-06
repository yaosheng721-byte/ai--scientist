from fastapi import APIRouter

from app.db.redis import redis_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    try:
        redis_status = "ok" if await redis_client.ping() else "unavailable"
    except Exception:
        redis_status = "unavailable"
    return {"api": "ok", "redis": redis_status}
