## Context

The login rate limiter currently uses `InMemorySlidingWindowRateLimiter`, which stores per-key event deques in-process. This state is lost on restart and not shared across workers. The `RateLimiter` protocol exposes sync `check(key) -> bool` and `record(key) -> None` methods. The auth router calls these synchronously from async handler code. The `arecord` method exists on the in-memory impl but is not part of the protocol.

A `# TODO: (REVIEW)` in `rate_limit.py` flags this as a known production gap.

## Goals / Non-Goals

**Goals:**
- Add a `RedisSlidingWindowRateLimiter` that shares state across workers and survives restarts
- Keep the existing `InMemorySlidingWindowRateLimiter` as the fallback when no Redis is configured
- Expose a shared async Redis client via a lazy singleton with proper lifecycle management
- Zero behavioral change for auth callers — same 429 behavior, same key structure

**Non-Goals:**
- Changing the sliding-window algorithm or the rate-limit behavior
- Adding rate limiting to any endpoint beyond login
- Redis Sentinel or Cluster support (single-instance Redis)
- Pool tuning or connection retry policies (defaults suffice)

## Decisions

### D1 — Make RateLimiter protocol async

The current protocol is sync (`def check`, `def record`). Since the Redis implementation requires async I/O, `check` and `record` become `async def`. The in-memory implementation trivially implements them as `async def` without doing I/O.

**Rationale**: Using `redis.asyncio.Redis` is the idiomatic async approach. Alternatives considered:
- **Sync `redis.Redis` in async context**: Blocks the event loop — unacceptable for a production API.
- **Thread pool executor**: Over-engineered for ~1ms Redis ops, adds complexity.
- **Separate sync/async protocol**: Two code paths to maintain, confusing.

Auth router call sites change from `limiter.check(key)` to `await limiter.check(key)` — mechanical, no behavioral change.

### D2 — Redis sorted sets for the sliding window

Each rate-limit key maps to a Redis sorted set where:
- **member**: `{timestamp}` (unique per hit — use `ZADD` with `NX` and a counter suffix or UUID to handle same-timestamp collisions)
- **score**: the monotonic timestamp value

Operations:
- `check(key)`: `ZREMRANGEBYSCORE(key, 0, now - window)` to evict, then `ZCARD(key)` to count
- `record(key)`: `ZADD(key, {score: now, member: unique_id})`

**Rationale**: Sorted sets provide exactly the primitives we need (range removal + cardinality) in O(log N) per operation. Alternatives considered:
- **TTL-based keys with INCR**: Each hit creates a separate key with TTL, sum key-space scan — more keys to manage, no window sliding.
- **LIST with LPUSH + LTRIM**: Harder to evict by time range. Sorted set `ZREMRANGEBYSCORE` maps directly to the eviction logic.

### D3 — Conditional factory

`get_login_rate_limiter()` checks `settings.REDIS_URL`:
- If set and non-empty → return `RedisSlidingWindowRateLimiter`
- If not set → return `InMemorySlidingWindowRateLimiter` (existing behavior)

**Rationale**: Zero-config local development keeps working. Production enables Redis via `.env`.

### D4 — Lazy singleton for Redis client

Follows the same pattern as `get_login_rate_limiter()`:
- Module-level `_redis_client: redis.asyncio.Redis | None = None`
- `get_redis_client()` creates on first call using `redis.asyncio.from_url(url)`
- `reset_redis_client()` test seam sets to `None`

**Rationale**: Consistent with existing codebase patterns. The client uses `redis.asyncio` which manages its own connection pool internally.

### D5 — Lifespan integration

The Redis client connects lazily on first use and closes explicitly via a lifespan shutdown handler. The client module exposes `close_redis_client()` for the lifespan shutdown.

**Rationale**: Explicit close ensures connections are cleaned up on graceful shutdown. No startup cost until Redis is actually used.

## Risks / Trade-offs

- **Async protocol change**: Auth router call sites need `await`. Mechanical change, but any missed `await` is caught by the type checker.
- **Redis unavailable at startup**: The factory returns `InMemorySlidingWindowRateLimiter` if `REDIS_URL` is empty, but if configured and Redis is down, `check()`/`record()` will raise. Mitigation: configure health checks and a Redis-sidekiq connection retry on the client.
- **fakeredis divergence**: `fakeredis` mimics `redis.asyncio` but edge cases may differ. Mitigation: integration tests in staging use a real Redis.
- **TTL cleanup**: Unlike the in-memory impl that auto-evicts on each operation, Redis sorted sets have no TTL. Keys for stale IP/email combos accumulate if a key is never accessed again. Acceptable: login keys are few, memory cost is negligible. Could add a key-level TTL via `EXPIRE` after `ZREMRANGEBYSCORE` if needed.
