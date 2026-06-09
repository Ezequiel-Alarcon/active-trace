## ADDED Requirements

### Requirement: Tenant model is the root of all domain entities

The system SHALL provide a `tenant` table as the root of the multi-tenant data model. Every other domain table introduced in subsequent changes MUST reference `tenant.id` via a non-nullable foreign key and MUST be reachable from a `tenant` row through that FK. A query that returns rows from a domain table without a joinable `tenant` is a data-model violation and MUST fail review.

The `tenant` table MUST contain at minimum:

- `id`: UUID primary key, default `uuid4()`.
- `codigo`: short unique identifier (e.g. `"UBA_FCEN"`). Globally unique, even across soft-deleted rows.
- `nombre`: human-readable name.
- `estado`: enum with values `Activo` and `Inactivo`.
- `created_at`, `updated_at`, `deleted_at`: standard timestamp columns provided by the mixins.

#### Scenario: A new tenant can be created

- **WHEN** the system creates a `tenant` row with `codigo="UBA_FCEN"`, `nombre="Facultad de Ciencias Exactas"`, `estado="Activo"`
- **THEN** the row is persisted with a UUID `id`, `created_at` and `updated_at` set to the current time, `deleted_at` is null, and the `tenant` table has exactly one row for that `codigo`

#### Scenario: A duplicate `codigo` is rejected at the database level

- **WHEN** the system attempts to insert a second `tenant` row with the same `codigo` as an existing one
- **THEN** the database raises a unique-constraint violation and no second row is persisted

#### Scenario: A tenant can be soft-deleted

- **WHEN** the system soft-deletes a `tenant` row
- **THEN** its `deleted_at` is set to the current time, the row is hidden from default `list` queries, and the row can be restored by clearing `deleted_at`

### Requirement: TenantScopedMixin provides UUID id, tenant_id, and timestamps to every domain model

The system SHALL provide a `TenantScopedMixin` that any domain model MAY inherit. The mixin MUST provide exactly these columns:

- `id`: UUID, primary key, default `uuid4()`.
- `tenant_id`: UUID, NOT NULL, foreign key to `tenant.id` with `ON DELETE RESTRICT`.
- `created_at`: timestamp with time zone, server-side default `now()`.
- `updated_at`: timestamp with time zone, server-side default `now()` and `ON UPDATE now()`.
- `deleted_at`: nullable timestamp with time zone, default `null` (soft delete).

The mixin MUST add a non-unique index on `tenant_id` and a composite index on `(tenant_id, deleted_at)`. A model inheriting the mixin MUST NOT override the type or nullability of `id` or `tenant_id`; if it does, code review MUST reject the change.

#### Scenario: Inserting a row without `tenant_id` fails

- **WHEN** a domain model that inherits `TenantScopedMixin` is inserted without an explicit `tenant_id` and no default is set
- **THEN** the database raises a not-null violation and the row is not persisted

#### Scenario: Inserting a row with a non-existent `tenant_id` fails

- **WHEN** a domain model that inherits `TenantScopedMixin` is inserted with a `tenant_id` that does not exist in the `tenant` table
- **THEN** the database raises a foreign-key violation and the row is not persisted

#### Scenario: `created_at` and `updated_at` are populated automatically

- **WHEN** a domain model row is inserted
- **THEN** `created_at` and `updated_at` are set to the current server time without the application having to set them

- **WHEN** a domain model row is updated
- **THEN** `updated_at` is automatically refreshed to the current server time

### Requirement: `tenant_id` is resolved from the session, never from request data

The system MUST resolve the current `tenant_id` exclusively from the authenticated session. The `tenant_id` MUST NOT be accepted from the query string, path, body, or any other client-supplied field of an HTTP request. A helper `get_current_tenant_id()` MUST raise if no `TenantContext` is set for the current asyncio task, so that repositories operating outside a request (e.g. background jobs) fail loudly unless an explicit `TenantContext` is provided.

In C-02 the session-based resolver is wired via a FastAPI dependency that, in this change, takes the `tenant_id` from a header only for tests and for the smoke endpoint; C-03 replaces that with the verified JWT claim.

#### Scenario: Repository called without a `TenantContext` fails

- **WHEN** a repository method is invoked outside a request and no `TenantContext` has been set
- **THEN** the call raises an exception and no query reaches the database

#### Scenario: `tenant_id` provided in a request body is ignored by the resolver

- **WHEN** a request includes a `tenant_id` field in the body or query string
- **THEN** the session resolver uses the `tenant_id` from the authenticated session, not from the request

### Requirement: Tenant isolation is enforced by construction through the repository base

The system MUST expose a generic `TenantScopedRepository[T]` whose public methods (`get`, `list`, `create`, `update`, `soft_delete`, `restore`, `count`) all apply a `WHERE tenant_id = :current_tenant AND deleted_at IS NULL` filter. Cross-tenant operations MUST only be reachable through methods prefixed `unsafe_` (e.g. `unsafe_list_all`, `unsafe_get`). Each `unsafe_*` invocation MUST emit an audit event with action `TENANT_CROSS_QUERY`; in C-02 the audit emission goes through a seam (`audit_emit`) that C-05 will wire to the persistent `AuditLog`. Code in `services/` and `routers/` MUST NOT call `session.query(...)` directly; it MUST go through a repository.

#### Scenario: A read by `id` from the wrong tenant returns nothing

- **WHEN** a repository `get` is called with the `id` of a row that belongs to tenant B while the current session is for tenant A
- **THEN** the call returns `None` and no row is returned, even if the `id` exists in the database

#### Scenario: A `list` call never returns rows from other tenants

- **WHEN** tenant A's repository `list` is called
- **THEN** the result set contains only rows where `tenant_id == A_id AND deleted_at IS NULL`, regardless of how many rows exist in other tenants

#### Scenario: A `create` with the wrong `tenant_id` is rejected

- **WHEN** a service attempts to persist a model with `tenant_id = B` while the repository is bound to tenant A
- **THEN** the call raises a validation error and no row is persisted

#### Scenario: Direct `session.query(...)` outside `repositories/` is a review defect

- **WHEN** a code-review pass finds `session.query(` or `select(` in `app/services/` or `app/api/`
- **THEN** the change MUST be rejected and the query MUST be moved to a repository
