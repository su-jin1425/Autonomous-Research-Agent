from __future__ import annotations

import json
import time

from app.core.config import get_settings


class RedisService:
    _client_instance = None

    def __init__(self) -> None:
        self.settings = get_settings()
        self._memory: dict[str, tuple[int, float]] = {}

    async def ping(self) -> bool:
        client = await self.client()

        if client is None:
            return True

        await client.ping()

        return True

    async def increment_rate_limit(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        client = await self.client()

        if client is None:
            return self._increment_memory(
                key,
                limit=limit,
                window_seconds=window_seconds,
            )

        count = await client.incr(key)

        if count == 1:
            await client.expire(
                key,
                window_seconds,
            )

        return int(count) <= limit, int(count)

    async def publish_execution_update(
        self,
        query_id: str,
        payload: dict,
    ) -> None:
        client = await self.client()

        if client is None:
            return

        await client.publish(
            f"research:{query_id}",
            json.dumps(payload),
        )

    async def queue_size(
        self,
        queue_name: str = "celery",
    ) -> int:
        client = await self.client()

        if client is None:
            return 0

        return int(await client.llen(queue_name))

    async def subscribe(
        self,
        channel: str,
    ):
        client = await self.client()

        if client is None:
            return None

        pubsub = client.pubsub()

        await pubsub.subscribe(channel)

        return pubsub

    async def client(self):
        if RedisService._client_instance is not None:
            return RedisService._client_instance

        try:
            import redis.asyncio as redis
        except ImportError:
            return None

        RedisService._client_instance = redis.from_url(
            self.settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

        return RedisService._client_instance

    def _increment_memory(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        now = time.monotonic()

        count, expires_at = self._memory.get(
            key,
            (
                0,
                now + window_seconds,
            ),
        )

        if now > expires_at:
            count = 0
            expires_at = now + window_seconds

        count += 1

        self._memory[key] = (
            count,
            expires_at,
        )

        return count <= limit, count
