## ADDED Requirements

### Requirement: A single Axios client is the only path for backend calls

The system SHALL expose one centralized Axios instance at `@/shared/services/api`. All backend communication MUST go through this instance via hooks in feature `services/` folders. The instance MUST have a request interceptor that attaches the in-memory access token as `Authorization: Bearer <access_token>` when a token is present, and MUST NOT attach a token for the login, forgot, and reset endpoints.

#### Scenario: Authenticated request carries the access token

- **WHEN** a request is made through the centralized client while a session access token is present
- **THEN** the outgoing request includes the header `Authorization: Bearer <access_token>`

#### Scenario: Anonymous auth endpoints carry no access token

- **WHEN** a request is made to `POST /api/auth/login`, `POST /api/auth/forgot`, or `POST /api/auth/reset`
- **THEN** the outgoing request includes no `Authorization` header derived from a stale access token

### Requirement: The client refreshes tokens transparently on 401 and retries the original request

The response interceptor MUST detect a `401` response (that is not itself from `/api/auth/refresh` or `/api/auth/login`), trigger `POST /api/auth/refresh` to obtain a new token pair, update the in-memory access token, and retry the original failed request once with the new token. If the retry's refresh succeeds, the caller MUST receive the successful retried response and MUST NOT observe the intermediate `401`.

#### Scenario: A single 401 triggers a refresh and the original request succeeds on retry

- **WHEN** a request through the client receives `401` and the subsequent `POST /api/auth/refresh` returns a new token pair
- **THEN** the access token in memory is updated to the new value
- **AND** the original request is retried with the new access token
- **AND** the caller receives the successful retried response, never the intermediate `401`

#### Scenario: The refresh request itself is never recursively refreshed

- **WHEN** `POST /api/auth/refresh` returns `401`
- **THEN** the interceptor does NOT attempt to refresh again for that response
- **AND** the session is cleared and the app navigates to `/login`

### Requirement: Concurrent 401s share a single in-flight refresh (single-flight)

When multiple requests receive `401` while a refresh is already in progress, the client MUST NOT issue more than one `POST /api/auth/refresh`. All affected requests MUST await the same in-flight refresh promise and then retry with the resulting token.

#### Scenario: N concurrent 401s cause exactly one refresh call

- **WHEN** three concurrent requests each receive `401` and a refresh is triggered
- **THEN** exactly one `POST /api/auth/refresh` is sent
- **AND** all three original requests are retried after that single refresh resolves
- **AND** each retried request carries the same new access token

### Requirement: A failed refresh clears the session and 403 is surfaced without retry

If `POST /api/auth/refresh` fails (e.g. `401 AUTH_TOKEN_REVOKED` or `AUTH_TOKEN_EXPIRED`), the client MUST clear the in-memory session, reject the queued requests, and navigate to `/login`. A `403` response MUST be surfaced to the caller as a permission error and MUST NOT trigger a refresh or a retry.

#### Scenario: Refresh failure logs the user out

- **WHEN** the in-flight refresh returns `401`
- **THEN** the in-memory access token is cleared
- **AND** all queued requests are rejected
- **AND** the app navigates to `/login`

#### Scenario: A 403 is not retried and not refreshed

- **WHEN** a request through the client receives `403`
- **THEN** no refresh is attempted
- **AND** the original request is not retried
- **AND** the caller receives a permission error
