"""Lazy singleton async Redis client (C-27).

Pattern: module-level global + get/reset/close functions, same as
`app.core.dependencies` for the database engine.
"""

from __future__ import annotations

import redis.asyncio as aioredis

_redis_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    """Lazy singleton: build client from Settings.REDIS_URL on first call."""
    global _redis_client
    if _redis_client is None:
        from app.core.config import get_settings

        settings = get_settings()
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return _redis_client


def reset_redis_client() -> None:
    """Test seam: drop the cached client so the next call rebuilds it."""
    global _redis_client
    _redis_client = None


async def close_redis_client() -> None:
    """Shutdown helper: close the connection pool if the client exists."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
    _redis_client = None
