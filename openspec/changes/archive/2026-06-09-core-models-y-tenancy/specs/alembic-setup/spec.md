## ADDED Requirements

### Requirement: Alembic is configured for async migrations and a strict naming convention

The system MUST ship an Alembic configuration that uses async SQLAlchemy (i.e. runs migrations against an `AsyncEngine` and uses `asyncpg` as the driver). The `env.py` MUST read the database URL from the same `Settings` used by the application, and MUST NOT hard-code a different URL.

The system MUST enforce the following naming convention for any object created by a migration:

- Primary key: `pk_<table>`.
- Foreign key: `fk_<table>_<referenced_table>` (multiple FKs may append an ordinal).
- Unique constraint: `uq_<table>_<column_set>` (snake_case column set joined by `_`).
- Check constraint: `ck_<table>_<column>`.
- Index: `ix_<table>_<column_set>` (non-unique) and `ux_<table>_<column_set>` (unique).

A migration that creates an object whose name does not follow the convention MUST fail the lint check configured for the project. The script template (`script.py.mako`) MUST contain a comment reminding developers that any new domain table MUST inherit `TenantScopedMixin` (and therefore include `tenant_id` and `deleted_at`).

#### Scenario: `alembic upgrade head` succeeds against an empty database

- **WHEN** `alembic upgrade head` is run against a database with no `alembic_version` row
- **THEN** the migrations apply, the `alembic_version` table records the head revision, and the resulting schema matches the model definitions

#### Scenario: `alembic downgrade -1` reverts the last migration

- **WHEN** `alembic downgrade -1` is run after `alembic upgrade head`
- **THEN** the last migration is reverted, the schema returns to the previous state, and no data is corrupted (the `001_tenant` migration is reversible in C-02)

#### Scenario: The naming convention lint catches a non-conforming index name

- **WHEN** a developer writes a migration that creates an index named `idx_usuario_email` instead of `ix_usuario_email`
- **THEN** the migration lint check fails and the PR cannot be merged

### Requirement: Migration `001_tenant` creates the `tenant` table

The migration `001_tenant.py` MUST create the `tenant` table with the columns defined in the `tenancy-foundation` spec (`id`, `codigo`, `nombre`, `estado`, `created_at`, `updated_at`, `deleted_at`) and the corresponding constraints and indexes following the naming convention. The migration MUST be reversible: `downgrade()` MUST drop the table and all its constraints.

The migration MUST be the only change applied by `alembic upgrade head` in a fresh database at the end of C-02. The Alembic head revision after C-02 lands MUST point to `001_tenant` (or its descendant if a hotfix revision is added in the same change).

#### Scenario: Migration creates the `tenant` table with the right columns

- **WHEN** `alembic upgrade head` is run on a fresh database
- **THEN** the `tenant` table exists with the columns `id`, `codigo`, `nombre`, `estado`, `created_at`, `updated_at`, `deleted_at`, with the correct types and nullability

#### Scenario: Migration creates the global unique index on `codigo`

- **WHEN** the `001_tenant` migration is applied
- **THEN** a unique index named `ux_tenant_codigo` exists on `(codigo)`, including soft-deleted rows (i.e. the unique constraint is full, not partial)

#### Scenario: Migration creates the timestamp indexes

- **WHEN** the `001_tenant` migration is applied
- **THEN** an index named `ix_tenant_created_at` exists on `(created_at)` and an index named `ix_tenant_deleted_at` exists on `(deleted_at)` to support time-window queries

#### Scenario: Migration is reversible

- **WHEN** `alembic downgrade -1` is run after the migration is applied
- **THEN** the `tenant` table is dropped with all its indexes and constraints, and a subsequent `alembic upgrade head` recreates the table in the same shape
