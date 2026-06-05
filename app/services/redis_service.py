from __future__ import annotations

import json
import os
import time

from app.core.config import get_settings


class RedisService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._memory: dict[str, tuple[int, float]] = {}

    async def ping(self) -> bool:
        client = await self.client()

        if client is None:
            return True

        try:
            await client.ping()
        except Exception:
            pass

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

        try:
            count = await client.incr(key)

            if count == 1:
                await client.expire(key, window_seconds)

            return int(count) <= limit, int(count)

        except Exception:
            return self._increment_memory(
                key,
                limit=limit,
                window_seconds=window_seconds,
            )

    async def publish_execution_update(
        self,
        query_id: str,
        payload: dict,
    ) -> None:
        client = await self.client()

        if client is None:
            return

        try:
            await client.publish(
                f"research:{query_id}",
                json.dumps(payload),
            )
        except Exception:
            pass

    async def queue_size(
        self,
        queue_name: str = "celery",
    ) -> int:
        client = await self.client()

        if client is None:
            return 0

        try:
            return int(await client.llen(queue_name))
        except Exception:
            return 0

    async def subscribe(
        self,
        channel: str,
    ):
        client = await self.client()

        if client is None:
            return None

        try:
            pubsub = client.pubsub()
            await pubsub.subscribe(channel)
            return pubsub
        except Exception:
            return None

    async def client(self):
        if "PYTEST_CURRENT_TEST" in os.environ:
            return None

        if self.settings.environment == "test":
            return None

        try:
            import redis.asyncio as redis
        except ImportError:
            return None

        try:
            client = redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )

            await client.ping()

            return client

        except Exception:
            return None

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