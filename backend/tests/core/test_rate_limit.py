"""Strict TDD for app.core.rate_limit (C-03 §1, D4).

Spec contract:
- `RateLimiter` is a Protocol with `check(key) -> bool` and `record(key) -> None`.
- `InMemorySlidingWindowRateLimiter(limit, window_seconds)`:
  - `check` returns True while the count of recorded events within the window is < limit.
  - `record(key)` adds `now()` to the deque for `key`.
  - `check` does NOT add (purely read).
  - Entries older than `window_seconds` are evicted before counting.
  - Different keys are independent (one key's traffic doesn't affect another).
  - Concurrency: the limiter is safe under concurrent `check`/`record` for the same key.
"""

from __future__ import annotations

import asyncio

import pytest

pytestmark = pytest.mark.no_db

from app.core.rate_limit import (
    InMemorySlidingWindowRateLimiter,
    RateLimiter,
)


def test_rate_limiter_protocol_is_satisfied_by_default_impl() -> None:
    impl: RateLimiter = InMemorySlidingWindowRateLimiter(limit=5, window_seconds=60)
    assert hasattr(impl, "check")
    assert hasattr(impl, "record")


def test_check_within_limit_returns_true_when_below_threshold() -> None:
    limiter = InMemorySlidingWindowRateLimiter(limit=3, window_seconds=60)
    assert limiter.check(("1.2.3.4", "a@b.com")) is True
    limiter.record(("1.2.3.4", "a@b.com"))
    assert limiter.check(("1.2.3.4", "a@b.com")) is True
    limiter.record(("1.2.3.4", "a@b.com"))
    assert limiter.check(("1.2.3.4", "a@b.com")) is True


def test_check_at_limit_returns_false() -> None:
    """Once `limit` events are recorded in the window, check returns False."""
    limiter = InMemorySlidingWindowRateLimiter(limit=3, window_seconds=60)
    for _ in range(3):
        limiter.record(("1.2.3.4", "a@b.com"))
    assert limiter.check(("1.2.3.4", "a@b.com")) is False


def test_check_does_not_consume_budget() -> None:
    """`check` is a read; it must not add to the counter."""
    limiter = InMemorySlidingWindowRateLimiter(limit=2, window_seconds=60)
    limiter.record(("1.2.3.4", "a@b.com"))
    for _ in range(50):
        assert limiter.check(("1.2.3.4", "a@b.com")) is True


def test_old_entries_evicted_from_window() -> None:
    """Events older than `window_seconds` must be dropped from the count."""
    limiter = InMemorySlidingWindowRateLimiter(limit=2, window_seconds=1)
    limiter._now = lambda: 1000.0  # type: ignore[assignment]
    limiter.record(("1.2.3.4", "a@b.com"))
    limiter.record(("1.2.3.4", "a@b.com"))
    # Move the clock past the window
    limiter._now = lambda: 1005.0  # type: ignore[assignment]
    # Old entries expired; the key now has a fresh budget
    assert limiter.check(("1.2.3.4", "a@b.com")) is True
    limiter.record(("1.2.3.4", "a@b.com"))
    limiter.record(("1.2.3.4", "a@b.com"))
    assert limiter.check(("1.2.3.4", "a@b.com")) is False


def test_keys_are_independent() -> None:
    """One key's traffic must not affect another key's budget."""
    limiter = InMemorySlidingWindowRateLimiter(limit=1, window_seconds=60)
    limiter.record(("1.2.3.4", "a@b.com"))
    assert limiter.check(("1.2.3.4", "a@b.com")) is False
    # Different key still has full budget
    assert limiter.check(("5.6.7.8", "a@b.com")) is True
    assert limiter.check(("1.2.3.4", "x@y.com")) is True


def test_concurrent_record_does_not_exceed_limit_count() -> None:
    """50 concurrent `record` calls for the same key produce exactly 50 entries
    (no corruption). The first 5 `check`s after recording all reflect a full window.
    """
    limiter = InMemorySlidingWindowRateLimiter(limit=5, window_seconds=60)

    async def _race() -> None:
        await asyncio.gather(
            *[limiter.arecord(("1.2.3.4", "a@b.com")) for _ in range(50)]
        )

    asyncio.run(_race())
    assert limiter.check(("1.2.3.4", "a@b.com")) is False


def test_check_does_not_evict_for_other_keys() -> None:
    """Eviction happens per-key, not across the whole store."""
    limiter = InMemorySlidingWindowRateLimiter(limit=1, window_seconds=1)
    limiter._now = lambda: 1000.0  # type: ignore[assignment]
    limiter.record(("ip1", "a@b.com"))
    limiter.record(("ip2", "a@b.com"))
    limiter._now = lambda: 1000.5  # type: ignore[assignment]
    # Both keys still within window
    assert limiter.check(("ip1", "a@b.com")) is False
    assert limiter.check(("ip2", "a@b.com")) is False
    # Move past window
    limiter._now = lambda: 1005.0  # type: ignore[assignment]
    assert limiter.check(("ip1", "a@b.com")) is True
    assert limiter.check(("ip2", "a@b.com")) is True


def test_record_after_expiry_resets_budget() -> None:
    limiter = InMemorySlidingWindowRateLimiter(limit=1, window_seconds=1)
    limiter._now = lambda: 1000.0  # type: ignore[assignment]
    limiter.record(("1.2.3.4", "a@b.com"))
    assert limiter.check(("1.2.3.4", "a@b.com")) is False
    limiter._now = lambda: 1005.0  # type: ignore[assignment]
    limiter.record(("1.2.3.4", "a@b.com"))
    assert limiter.check(("1.2.3.4", "a@b.com")) is False
