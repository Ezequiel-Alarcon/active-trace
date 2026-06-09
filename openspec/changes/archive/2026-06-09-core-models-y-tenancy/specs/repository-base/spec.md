## ADDED Requirements

### Requirement: A generic `TenantScopedRepository[T]` is the only path for domain queries

The system MUST provide a generic `TenantScopedRepository[T]` parameterized by the ORM model. The repository MUST be constructed with an `AsyncSession` and a `tenant_id` (UUID), both required. Public methods (`get`, `list`, `create`, `update`, `soft_delete`, `restore`, `count`) MUST apply the tenant filter and the `deleted_at IS NULL` filter to every query. Cross-tenant operations MUST only be reachable through methods prefixed `unsafe_` (`unsafe_get`, `unsafe_list_all`, `unsafe_count`, `unsafe_soft_delete`, `unsafe_restore`, and a clearly-named `unsafe_physical_delete`).

The repository MUST also provide:

- `get_by_id(id: UUID) -> T | None`
- `list(*, limit: int = 50, offset: int = 0, order_by: list[...] | None = None, filters: list[...] | None = None) -> list[T]`
- `create(data: dict | T) -> T`
- `update(obj: T, data: dict) -> T`
- `soft_delete(obj: T) -> None`
- `restore(obj: T) -> None`
- `count(*, filters: list[...] | None = None) -> int`

The repository MUST refuse to be constructed without a `tenant_id`. The constructor MUST raise if `tenant_id is None`.

#### Scenario: Repository requires a tenant_id at construction

- **WHEN** `TenantScopedRepository(session=session, model=T, tenant_id=None)` is called
- **THEN** the constructor raises and the repository is not usable

#### Scenario: `get_by_id` returns the row only if it belongs to the current tenant

- **WHEN** `repo.get_by_id(id=X)` is called and there exists a row with that `id` whose `tenant_id` equals the repository's tenant
- **THEN** the row is returned

- **WHEN** `repo.get_by_id(id=X)` is called and there exists a row with that `id` whose `tenant_id` differs from the repository's tenant
- **THEN** the method returns `None` and no row is returned

- **WHEN** `repo.get_by_id(id=X)` is called and the row exists but `deleted_at IS NOT NULL`
- **THEN** the method returns `None` and no row is returned

#### Scenario: `list` paginates and orders correctly within the tenant

- **WHEN** a tenant has 120 active rows in the model
- **THEN** `repo.list(limit=50, offset=0)` returns the first 50 ordered by the default order, `offset=50` returns the next 50, and `offset=100` returns the last 20
- **AND** no row from another tenant appears in the result set

#### Scenario: `create` persists a row bound to the repository's tenant

- **WHEN** `repo.create({...})` is called
- **THEN** the persisted row has `tenant_id` equal to the repository's tenant, `created_at` and `updated_at` set to the current server time, and `deleted_at IS NULL`

#### Scenario: `create` rejects a mismatched tenant_id

- **WHEN** `repo.create({"tenant_id": OTHER, ...})` is called on a repository bound to tenant A
- **THEN** the call raises a validation error and no row is persisted

#### Scenario: `update` refreshes `updated_at` and preserves `tenant_id`

- **WHEN** `repo.update(obj, {...})` is called
- **THEN** the row's `updated_at` is set to the current server time, the row's `tenant_id` does not change, and the rest of the fields reflect the provided data

#### Scenario: `soft_delete` and `restore` transition `deleted_at`

- **WHEN** `repo.soft_delete(obj)` is called
- **THEN** the row's `deleted_at` is set to the current server time and the row is no longer returned by `get_by_id`/`list`/`count`

- **WHEN** `repo.restore(obj)` is called on the same row afterwards
- **THEN** the row's `deleted_at` is cleared and the row is again returned by `get_by_id`/`list`/`count`

### Requirement: Cross-tenant operations are explicit and audited

Methods prefixed `unsafe_` MUST bypass the tenant filter and/or the `deleted_at IS NULL` filter. Each `unsafe_*` call MUST emit an audit event through the `audit_emit` seam with a distinct action code (`TENANT_CROSS_QUERY`, `ROW_INCLUDE_DELETED`, `ROW_HARD_DELETE`). The methods MUST be visually distinct (prefix `unsafe_`) and MUST live in a separate module section to make accidental use obvious in code review.

#### Scenario: `unsafe_list_all` returns rows from all tenants and emits audit

- **WHEN** `repo.unsafe_list_all()` is called
- **THEN** the result set includes rows from all tenants (subject to the `deleted_at` policy the method specifies) and the call emits an audit event with action `TENANT_CROSS_QUERY`

#### Scenario: `unsafe_physical_delete` removes the row and emits audit

- **WHEN** `repo.unsafe_physical_delete(obj)` is called
- **THEN** the row is hard-deleted from the database and the call emits an audit event with action `ROW_HARD_DELETE`

### Requirement: Repositories are constructed through a single factory

The system MUST provide a factory `get_tenant_repository(model: type[T], session: AsyncSession) -> TenantScopedRepository[T]` that resolves the current `tenant_id` from the request-scoped `TenantContext` and returns a repository bound to that tenant. The factory MUST be the only way `services/` and `routers/` obtain a repository. Constructing a repository directly in a service (with `TenantScopedRepository(...)`) is allowed only in tests; production code MUST use the factory.

#### Scenario: Service obtains a repository through the factory

- **WHEN** a service method needs to read rows of model `M`
- **THEN** it calls `get_tenant_repository(M, session)` and uses the returned repository — it does not call `TenantScopedRepository` directly with a hard-coded `tenant_id`

#### Scenario: Factory uses the current `TenantContext`

- **WHEN** a service is invoked within a request whose `TenantContext` is `tenant_id=A`
- **THEN** the repository returned by the factory is bound to `tenant_id=A`, and any read it performs is filtered by `A`
