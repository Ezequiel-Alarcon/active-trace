"""Rate limiting primitives (C-03 §1, D4).

`RateLimiter` is the protocol the auth router uses; the in-memory implementation
is the default and is swappable for a Redis-backed one in a future change.

Window model: sliding window. Each (key, timestamp) is stored in a deque; entries
older than `window_seconds` are evicted before the count is compared to `limit`.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RateLimiter(Protocol):
    """Returns True if a request is allowed under the limit."""

    def check(self, key: Any) -> bool: ...

    def record(self, key: Any) -> None: ...


class InMemorySlidingWindowRateLimiter:
    """Default in-process limiter. Safe for concurrent use on the same key."""

    def __init__(self, *, limit: int, window_seconds: float) -> None:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        self._limit = limit
        self._window = float(window_seconds)
        self._events: dict[Any, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    def _now(self) -> float:
        return time.monotonic()

    def _evict(self, key: Any, now: float) -> None:
        cutoff = now - self._window
        dq = self._events[key]
        while dq and dq[0] <= cutoff:
            dq.popleft()
        if not dq:
            self._events.pop(key, None)

    def check(self, key: Any) -> bool:
        now = self._now()
        self._evict(key, now)
        return len(self._events.get(key, ())) < self._limit

    def record(self, key: Any) -> None:
        now = self._now()
        self._evict(key, now)
        self._events[key].append(now)

    async def arecord(self, key: Any) -> None:
        async with self._lock:
            self.record(key)


_login_limiter: RateLimiter | None = None


def get_login_rate_limiter() -> RateLimiter:
    """Lazy singleton: build the default in-memory login limiter from settings."""
    global _login_limiter
    if _login_limiter is None:
        from app.core.config import get_settings

        settings = get_settings()
        _login_limiter = InMemorySlidingWindowRateLimiter(
            limit=settings.LOGIN_RATE_LIMIT_PER_MINUTE,
            window_seconds=settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS,
        )
    return _login_limiter


def reset_login_rate_limiter() -> None:
    """Test seam: drop the cached limiter so the next call rebuilds it."""
    global _login_limiter
    _login_limiter = None
