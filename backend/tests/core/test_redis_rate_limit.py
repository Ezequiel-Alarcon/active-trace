"""Strict TDD for RedisSlidingWindowRateLimiter (C-27).

Spec contract:
- RedisSlidingWindowRateLimiter satisfies the RateLimiter Protocol
- check returns True while count of recorded events within the window is < limit
- record adds an entry to the Redis sorted set for the key
- check is a read-only operation (does not consume budget)
- Entries older than window_seconds are evicted before counting
- Different keys have independent budgets
- Concurrent record calls safely produce the expected count
- Redis client is a lazy singleton (creates once, caches)
- reset_redis_client() clears the cached instance
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from fakeredis import FakeAsyncRedis

from app.core import redis_client as rc
from app.core.rate_limit import (
    RateLimiter,
    RedisSlidingWindowRateLimiter,
)

pytestmark = pytest.mark.no_db


@pytest.fixture(autouse=True)
def _reset_redis_client() -> None:
    rc._redis_client = None


@pytest.fixture
def fake_redis() -> FakeAsyncRedis:
    return FakeAsyncRedis(decode_responses=True)


@pytest.fixture
def limiter(fake_redis: FakeAsyncRedis) -> RedisSlidingWindowRateLimiter:
    rc._redis_client = fake_redis
    return RedisSlidingWindowRateLimiter(limit=5, window_seconds=60)


# --- 6.2 Protocol conformance ---

def test_redis_limiter_protocol_conformance() -> None:
    rc._redis_client = FakeAsyncRedis(decode_responses=True)
    impl: RateLimiter = RedisSlidingWindowRateLimiter(limit=5, window_seconds=60)
    assert isinstance(impl, RateLimiter)


# --- 6.3 Within limit ---

async def test_check_within_limit_returns_true(limiter: RedisSlidingWindowRateLimiter) -> None:
    assert await limiter.check(("1.2.3.4", "a@b.com")) is True
    await limiter.record(("1.2.3.4", "a@b.com"))
    assert await limiter.check(("1.2.3.4", "a@b.com")) is True


# --- 6.4 At limit ---

async def test_check_at_limit_returns_false(limiter: RedisSlidingWindowRateLimiter) -> None:
    for _ in range(5):
        await limiter.record(("1.2.3.4", "a@b.com"))
    assert await limiter.check(("1.2.3.4", "a@b.com")) is False


# --- 6.5 Check does not consume budget ---

async def test_check_does_not_consume_budget(limiter: RedisSlidingWindowRateLimiter) -> None:
    await limiter.record(("1.2.3.4", "a@b.com"))
    for _ in range(50):
        assert await limiter.check(("1.2.3.4", "a@b.com")) is True


# --- 6.6 Old entries evicted from window ---

async def test_old_entries_evicted_from_window() -> None:
    limiter = RedisSlidingWindowRateLimiter(limit=2, window_seconds=1)
    rc._redis_client = FakeAsyncRedis(decode_responses=True)
    limiter._now = lambda: 1000.0  # type: ignore[assignment]
    await limiter.record(("1.2.3.4", "a@b.com"))
    await limiter.record(("1.2.3.4", "a@b.com"))
    limiter._now = lambda: 1005.0  # type: ignore[assignment]
    assert await limiter.check(("1.2.3.4", "a@b.com")) is True
    await limiter.record(("1.2.3.4", "a@b.com"))
    await limiter.record(("1.2.3.4", "a@b.com"))
    assert await limiter.check(("1.2.3.4", "a@b.com")) is False


# --- 6.7 Keys are independent ---

async def test_keys_are_independent() -> None:
    limiter = RedisSlidingWindowRateLimiter(limit=1, window_seconds=60)
    rc._redis_client = FakeAsyncRedis(decode_responses=True)
    await limiter.record(("1.2.3.4", "a@b.com"))
    assert await limiter.check(("1.2.3.4", "a@b.com")) is False
    assert await limiter.check(("5.6.7.8", "a@b.com")) is True
    assert await limiter.check(("1.2.3.4", "x@y.com")) is True


# --- 6.8 Concurrent record ---

async def test_concurrent_record_does_not_exceed_limit() -> None:
    limiter = RedisSlidingWindowRateLimiter(limit=5, window_seconds=60)
    rc._redis_client = FakeAsyncRedis(decode_responses=True)

    async def _record_one() -> None:
        await limiter.record(("1.2.3.4", "a@b.com"))

    await asyncio.gather(*[_record_one() for _ in range(50)])
    assert await limiter.check(("1.2.3.4", "a@b.com")) is False


# --- 6.9 Redis client lazy singleton ---

def test_redis_client_lazy_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    rc._redis_client = None
    fake = FakeAsyncRedis(decode_responses=True)
    monkeypatch.setattr("redis.asyncio.from_url", lambda url, **kwargs: fake)
    client1 = rc.get_redis_client()
    client2 = rc.get_redis_client()
    assert client1 is client2
    assert client1 is fake


# --- 6.10 Redis client reset clears cached instance ---

def test_redis_client_reset_clears_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    rc._redis_client = None
    fakes: list[FakeAsyncRedis] = []

    def _fake_from_url(url: str, **kwargs: Any) -> FakeAsyncRedis:
        f = FakeAsyncRedis(decode_responses=True)
        fakes.append(f)
        return f

    monkeypatch.setattr("redis.asyncio.from_url", _fake_from_url)
    client1 = rc.get_redis_client()
    rc.reset_redis_client()
    client2 = rc.get_redis_client()
    assert client1 is not client2
    assert len(fakes) == 2
