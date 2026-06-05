import pytest

from app.services.redis_service import RedisService


@pytest.mark.asyncio
async def test_redis_service_falls_back_to_memory_for_rate_limits() -> None:
    service = RedisService()

    first = await service.increment_rate_limit(
        "rate-limit:test",
        limit=2,
        window_seconds=60,
    )
    second = await service.increment_rate_limit(
        "rate-limit:test",
        limit=2,
        window_seconds=60,
    )
    third = await service.increment_rate_limit(
        "rate-limit:test",
        limit=2,
        window_seconds=60,
    )

    assert first == (True, 1)
    assert second == (True, 2)
    assert third == (False, 3)


@pytest.mark.asyncio
async def test_redis_service_gracefully_handles_missing_client() -> None:
    service = RedisService()

    print("ENV:", service.settings.environment)
    print("REDIS_URL:", service.settings.redis_url)
    print("CLIENT:", await service.client())

    assert await service.ping() is True
    assert await service.queue_size() == 0
    assert await service.subscribe("research:test") is None

    await service.publish_execution_update(
        "query-1",
        {"status": "completed"},
    )