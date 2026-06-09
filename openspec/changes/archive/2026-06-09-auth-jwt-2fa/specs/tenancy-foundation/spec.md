## MODIFIED Requirements

### Requirement: `tenant_id` is resolved from the session, never from request data

The system MUST resolve the current `tenant_id` exclusively from the authenticated session. The `tenant_id` MUST NOT be accepted from the query string, path, body, or any other client-supplied field of an HTTP request. A helper `get_current_tenant_id()` MUST raise if no `TenantContext` is set for the current asyncio task, so that repositories operating outside a request (e.g. background jobs) fail loudly unless an explicit `TenantContext` is provided.

In C-02 the session-based resolver was wired via a FastAPI dependency that read the `tenant_id` from an `X-Tenant-Id` header for tests and the smoke endpoint. C-03 replaces that placeholder with a resolver that reads `tenant_id` from the verified JWT claim `tid` via the `get_current_user` dependency. The `TenantContext` shape and the `get_current_tenant_id()` contract do NOT change.

#### Scenario: Repository called without a `TenantContext` fails

- **WHEN** a repository method is invoked outside a request and no `TenantContext` has been set
- **THEN** the call raises an exception and no query reaches the database

#### Scenario: `tenant_id` provided in a request body is ignored by the resolver

- **WHEN** a request includes a `tenant_id` field in the body or query string
- **THEN** the session resolver uses the `tenant_id` from the authenticated session, not from the request

#### Scenario: `tenant_id` provided in the legacy `X-Tenant-Id` header is ignored

- **WHEN** a request carries an `X-Tenant-Id` header with a value that differs from the `tid` claim of the verified JWT
- **THEN** the session resolver uses the `tid` from the verified JWT, not the header
- **AND** the header is silently ignored (no error, no log line that names the user or the value)

#### Scenario: A request with a valid JWT and no `X-Tenant-Id` header resolves the tenant from the token

- **WHEN** a request carries a valid access JWT with `tid = T1` and no `X-Tenant-Id` header
- **THEN** the session resolver sets `TenantContext(tenant_id=T1)` on the per-task ContextVar
- **AND** `get_current_tenant_id()` returns `T1`
