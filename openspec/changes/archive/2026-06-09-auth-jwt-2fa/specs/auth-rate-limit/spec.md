## ADDED Requirements

### Requirement: The system provides a swappable in-memory sliding-window rate limiter

The system MUST expose a `RateLimiter` protocol in `app/core/rate_limit.py` with two methods: `async def check(self, key: tuple[str, str], *, limit: int, window_seconds: int) -> bool` (returns `True` if the request may proceed, `False` if the limit has been exceeded) and `async def record(self, key: tuple[str, str]) -> None` (records a hit on the key, regardless of outcome). The protocol MUST be the only contract that auth code uses to gate the login endpoint.

The system MUST also expose a default in-memory implementation `InMemorySlidingWindowRateLimiter` that:

- Stores, per key, a `deque[float]` of monotonic timestamps of recent hits.
- `check` trims entries older than `now - window_seconds` and returns `len(deque) < limit`.
- `record` appends `time.monotonic()` to the deque and trims the same way.
- Cleans up keys whose deque is empty on a background task (or on `record` for the affected key only — at minimum, no leak under sustained traffic).
- Is safe for concurrent asyncio tasks (uses a single `asyncio.Lock` or per-key `asyncio.Lock`).

The implementation MUST be replaceable by a future Redis-backed implementation without changing the call sites. Tests MUST exercise the in-memory implementation directly.

#### Scenario: A request within the limit is allowed

- **WHEN** a key has been hit `limit - 1` times in the last `window_seconds`
- **AND** `check` is called for the same key with the same `limit` and `window_seconds`
- **THEN** `check` returns `True`

#### Scenario: A request at the limit is rejected

- **WHEN** a key has been hit `limit` times in the last `window_seconds`
- **AND** `check` is called for the same key with the same `limit` and `window_seconds`
- **THEN** `check` returns `False`

#### Scenario: Old hits are evicted by the sliding window

- **WHEN** a key has been hit `limit` times, the oldest of which is older than `window_seconds`
- **AND** `check` is called for the same key with the same `limit` and `window_seconds`
- **THEN** `check` returns `True` (the old hit has been evicted)

#### Scenario: Different keys are tracked independently

- **WHEN** key `(ip=A, subject=B)` has been hit `limit` times
- **AND** `check` is called for key `(ip=A, subject=C)` with the same limit
- **THEN** `check` returns `True`

### Requirement: The login endpoint is rate-limited per client IP and email

`POST /api/auth/login` MUST be gated by the rate limiter, keyed on `(client_ip, email_lower)`. The login router MUST call `check` first; if `False` → respond `429` with `code = "AUTH_RATE_LIMITED"` and `Retry-After` header equal to the remaining seconds in the window. The router MUST call `record` after the request has been processed (regardless of whether the login succeeded or failed), so both successful and failed attempts count toward the limit.

The default limit is `Settings.LOGIN_RATE_LIMIT_PER_MINUTE` (default 5) within `Settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS` (default 60).

#### Scenario: The 6th login attempt from the same IP and email within 60s is rejected

- **WHEN** `POST /api/auth/login` has been called 5 times in the last 60s from the same `client_ip` and the same `email` (case-insensitive), with the 5 calls having been `record`ed
- **AND** a 6th call is made from the same `client_ip` and `email` within the window
- **THEN** the response is `429` with `code = "AUTH_RATE_LIMITED"` and `Retry-After` set to a value between 1 and 60
- **AND** the auth service is not called for that request (no Argon2id verification, no DB query for the user)
- **AND** no `AUTH_LOGIN_OK` or `AUTH_LOGIN_FAIL` is emitted for the 6th call

#### Scenario: The limit does not collide across different (IP, email) pairs

- **WHEN** `POST /api/auth/login` has been called 5 times in the last 60s from IP `A` and email `E1`
- **AND** a 6th call is made from the same IP `A` but a different email `E2`
- **THEN** the request is processed normally (not rate-limited)

#### Scenario: The limit does not collide across different IPs for the same email

- **WHEN** `POST /api/auth/login` has been called 5 times in the last 60s from IP `A` and email `E1`
- **AND** a 6th call is made from a different IP `B` and the same email `E1`
- **THEN** the request is processed normally (not rate-limited)

#### Scenario: Email comparison is case-insensitive

- **WHEN** a request is made with `email = "Alice@Example.com"` and counts toward the limit
- **AND** a subsequent request is made from the same IP with `email = "alice@example.com"`
- **THEN** the second request is treated as the same key and counts toward the same limit

#### Scenario: Both successful and failed logins count toward the limit

- **WHEN** 3 failed and 2 successful logins have been made from the same IP and email within 60s
- **THEN** the 6th attempt from the same IP and email is rejected with `429`
