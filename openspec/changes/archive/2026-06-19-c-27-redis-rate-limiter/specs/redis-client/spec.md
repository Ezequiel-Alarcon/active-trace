## ADDED Requirements

### Requirement: The system provides a lazy singleton async Redis client

The system MUST expose an async Redis client via `app/core/redis_client.py` with the following:

- `get_redis_client() -> redis.asyncio.Redis`: Returns a lazy singleton `redis.asyncio.Redis` instance. On first call, creates the client using `redis.asyncio.from_url(settings.REDIS_URL)` with `decode_responses=True`. Subsequent calls return the cached instance. Thread-safe for concurrent asyncio tasks.
- `reset_redis_client() -> None`: Test seam. Sets the cached instance to `None` so the next `get_redis_client()` call creates a fresh client.
- `close_redis_client() -> None`: Closes the underlying Redis connection pool if the client exists. Safe to call multiple times. Called during application shutdown.

The client MUST be configured via `Settings.REDIS_URL` (default `redis://localhost:6379/0`).

#### Scenario: First call creates a new client
- **WHEN** `get_redis_client()` is called for the first time
- **THEN** it creates a new `redis.asyncio.Redis` instance using `Settings.REDIS_URL`

#### Scenario: Subsequent calls return the cached client
- **WHEN** `get_redis_client()` has been called once
- **AND** it is called again
- **THEN** the same client instance is returned

#### Scenario: Reset clears the cached client
- **WHEN** `reset_redis_client()` is called
- **AND** `get_redis_client()` is called afterwards
- **THEN** a new client instance is created

#### Scenario: Close cleans up the connection pool
- **WHEN** a Redis client exists
- **AND** `close_redis_client()` is called
- **THEN** the connection pool is closed
- **AND** subsequent calls to `get_redis_client()` create a fresh client

### Requirement: Redis client is connected on startup and closed on shutdown

The application lifespan MUST call `get_redis_client()` on startup (to establish the connection pool) and `close_redis_client()` on shutdown.

#### Scenario: Client connects at startup
- **WHEN** the application starts
- **AND** `REDIS_URL` is configured
- **THEN** the Redis client connection pool is established

#### Scenario: Client closes at shutdown
- **WHEN** the application shuts down
- **THEN** the Redis connection pool is closed gracefully
