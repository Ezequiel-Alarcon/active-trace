## 1. Dependencies and Config

- [x] 1.1 Add `redis[hiredis]` to production dependencies in `backend/pyproject.toml`
- [x] 1.2 Add `fakeredis[lua]` to dev dependencies in `backend/pyproject.toml`
- [x] 1.3 Add `REDIS_URL: str = Field(default="redis://localhost:6379/0")` to `Settings` in `backend/app/core/config.py`

## 2. Redis Client Module

- [x] 2.1 Create `backend/app/core/redis_client.py` with `get_redis_client()` lazy singleton (using `redis.asyncio.from_url` with `decode_responses=True`), `reset_redis_client()` test seam, and `close_redis_client()` shutdown helper

## 3. Make RateLimiter Protocol Async

- [x] 3.1 Update `RateLimiter` protocol in `backend/app/core/rate_limit.py`: change `def check` → `async def check`, `def record` → `async def record`
- [x] 3.2 Update `InMemorySlidingWindowRateLimiter`: add `async def check` and `async def record` (trivially awaitable, same body), remove `arecord` (no longer needed)
- [x] 3.3 Update auth router call sites in `backend/app/auth/routers/auth.py`: `limiter.check(key)` → `await limiter.check(key)`, `limiter.record(key)` → `await limiter.record(key)`

## 4. Redis Sliding Window Rate Limiter

- [x] 4.1 Create `RedisSlidingWindowRateLimiter` in `backend/app/core/rate_limit.py` implementing `RateLimiter` protocol using Redis sorted sets (ZADD with unique member, ZREMRANGEBYSCORE for eviction, ZCARD for count)
- [x] 4.2 Add `_now()` and `_redis_key()` helpers on the class (same pattern as in-memory impl)
- [x] 4.3 Implement `async def check(key) -> bool`: evict old entries, return `ZCARD < limit`
- [x] 4.4 Implement `async def record(key) -> None`: evict old entries, ZADD with unique member

## 5. Conditional Factory and Lifespan

- [x] 5.1 Update `get_login_rate_limiter()` to check `settings.REDIS_URL`: if set → return `RedisSlidingWindowRateLimiter`, else → return `InMemorySlidingWindowRateLimiter`
- [x] 5.2 Register Redis client lifecycle in `backend/app/main.py` lifespan: call `get_redis_client()` on startup (warm connection pool), call `close_redis_client()` on shutdown

## 6. Tests

- [x] 6.1 Create `backend/tests/core/test_redis_rate_limit.py` with `pytest.mark.no_db`, using `fakeredis.asyncio.FakeRedis` (monkey-patched into `redis_client._redis_client`)
- [x] 6.2 Test: protocol conformance (`RedisSlidingWindowRateLimiter` satisfies `RateLimiter`)
- [x] 6.3 Test: within limit returns True
- [x] 6.4 Test: at limit returns False
- [x] 6.5 Test: check does not consume budget
- [x] 6.6 Test: old entries evicted from window (monkey-patch `_now()` for time control)
- [x] 6.7 Test: keys are independent
- [x] 6.8 Test: concurrent record does not exceed limit count
- [x] 6.9 Test: Redis client lazy singleton (first call creates, subsequent returns same)
- [x] 6.10 Test: Redis client reset clears cached instance
- [x] 6.11 Update existing `test_rate_limit.py` tests to use `async` test functions and `await` calls

## 7. Cleanup

- [x] 7.1 Remove the `# TODO: (REVIEW)` comment in `rate_limit.py` about replacing with Redis (now resolved)
