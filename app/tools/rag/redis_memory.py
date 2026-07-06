import json
from typing import Any

from app.db.redis import redis_client


class RedisMemoryStore:
    def __init__(self, namespace: str = "ai_scientist") -> None:
        self.namespace = namespace

    def _key(self, run_id: str, name: str) -> str:
        return f"{self.namespace}:run:{run_id}:{name}"

    async def set_json(self, run_id: str, name: str, value: dict[str, Any], ttl: int = 86400) -> None:
        await redis_client.set(self._key(run_id, name), json.dumps(value, ensure_ascii=False), ex=ttl)

    async def get_json(self, run_id: str, name: str) -> dict[str, Any] | None:
        raw = await redis_client.get(self._key(run_id, name))
        if raw is None:
            return None
        return json.loads(raw)
