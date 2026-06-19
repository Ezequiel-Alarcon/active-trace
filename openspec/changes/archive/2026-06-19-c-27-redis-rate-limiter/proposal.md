## Why

The current `InMemorySlidingWindowRateLimiter` resets on every process restart and does not share state across workers, making it ineffective in multi-worker production deployments. Adding a Redis-backed implementation provides a shared, persistent rate limit state that survives restarts and works across all workers.

## What Changes

- Add `redis[hiredis]` to production dependencies and `fakeredis[lua]` to dev dependencies
- Add `REDIS_URL` setting to `Settings` with default `redis://localhost:6379/0`
- Create `backend/app/core/redis_client.py` with lazy singleton Redis client (async) and test seam
- Create `RedisSlidingWindowRateLimiter` in `rate_limit.py` implementing the existing `RateLimiter` Protocol using Redis sorted sets
- Modify `get_login_rate_limiter()` to conditionally return `RedisSlidingWindowRateLimiter` when `REDIS_URL` is configured, falling back to in-memory
- Register Redis client lifecycle in the app's lifespan (connect on startup, close on shutdown)
- Add tests for `RedisSlidingWindowRateLimiter` using `fakeredis`
- Resolve the existing `# TODO: (REVIEW)` in `rate_limit.py`

## Capabilities

### New Capabilities
- `redis-client`: Lazy singleton async Redis client with connection management (connect on startup, close on shutdown) and test seam via `reset_redis_client()`

### Modified Capabilities
No spec-level requirement changes. The existing `RateLimiter` protocol and `auth-rate-limit` requirements remain unchanged — this is purely an implementation addition.

## Impact

- **New dependency**: `redis[hiredis]` (prod), `fakeredis[lua]` (dev)
- **New config**: `REDIS_URL` in Settings (`.env`)
- **New module**: `backend/app/core/redis_client.py`
- **Modified**: `backend/app/core/rate_limit.py` — add `RedisSlidingWindowRateLimiter`, conditional factory
- **Modified**: `backend/app/core/config.py` — add `REDIS_URL`
- **Modified**: `backend/app/core/lifespan.py` (or equivalent) — Redis lifecycle hooks
- **Modified**: `backend/pyproject.toml` — dependency entries
- **New tests**: `backend/tests/core/test_redis_rate_limit.py`
