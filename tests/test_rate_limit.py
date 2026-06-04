import pytest

from app.services.redis_service import RedisService


@pytest.mark.asyncio
async def test_memory_rate_limit_expires_and_resets() -> None:
    service = RedisService()

    allowed_one = await service.increment_rate_limit(
        "rate-limit:window",
        limit=1,
        window_seconds=1,
    )
    allowed_two = await service.increment_rate_limit(
        "rate-limit:window",
        limit=1,
        window_seconds=1,
    )

    assert allowed_one == (True, 1)
    assert allowed_two == (False, 2)
