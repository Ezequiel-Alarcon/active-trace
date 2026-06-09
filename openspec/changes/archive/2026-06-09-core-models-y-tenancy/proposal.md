## Why

El sistema activia-trace es multi-institución desde el día 0 (ADR-002 row-level), pero el esqueleto creado en `C-01 foundation-setup` todavía no tiene el `Tenant` raíz, el mixin de aislamiento, el contrato de soft delete, ni el helper de cifrado en reposo. Cada change posterior (auth, RBAC, entidades académicas, liquidaciones) necesita apoyarse sobre un cimiento multi-tenant inmutable. Si C-02 no fija estas primitivas ahora, cualquier error de aislamiento o de cifrado de PII queda propagado a todos los módulos del producto.

## What Changes

- Nuevo modelo `Tenant` raíz (UUID, `codigo` único global, `nombre`, `estado`, `created_at`/`updated_at`/`deleted_at`).
- Nuevo mixin `TenantScopedMixin` aplicado a todas las entidades de dominio: provee `id` (UUID), `tenant_id` (FK no nula), `created_at`, `updated_at`, `deleted_at` (soft delete), e índice único `(tenant_id, id)`.
- Nuevo mixin `SoftDeleteMixin` con columna `deleted_at` + query helper (filtro por defecto de filas no eliminadas) + métodos `soft_delete()` y `restore()` en el repository genérico.
- Nueva utility `core/security/crypto.py` con `encrypt(plaintext) -> bytes` y `decrypt(ciphertext) -> str` usando AES-256-GCM con clave derivada de `ENCRYPTION_KEY` (32 chars), IV aleatorio por cifrado, AAD con prefijo de tenant_id, y API que **nunca** loggea el contenido descifrado.
- Nuevo `core/tenancy.py` con `get_current_tenant_id()` (resolución desde sesión) y `TenantContext` (token tipado pasado a repositories).
- Nuevo `repositories/base.py` con `TenantScopedRepository[T]`: toda consulta filtra por `tenant_id` y por `deleted_at IS NULL` por defecto. Métodos `get`, `list`, `create`, `update`, `soft_delete`, `restore`, `count`. Métodos `*_unsafe_*` para casos administrativos (cruzan tenant) marcados explícitamente y registrados en audit log (C-05 proveerá el sink; aquí solo se deja el seam).
- Setup Alembic: `alembic.ini`, `alembic/env.py` con soporte async, convención de nombres (`ix_`, `uq_`, `fk_`, `ck_`, `pk_`), script template que fuerza incluir `tenant_id` y `deleted_at` en cada nueva tabla, y **Migración 001: tenant**.
- Configuración: `ENCRYPTION_KEY` agregada a `Settings` (Pydantic v2) con validación de longitud exacta 32 chars, fail-fast en startup.
- Tests: aislamiento multi-tenant (tenant A no ve/escribe datos de tenant B), soft delete (no aparece en list, sí en `*_unsafe_*`), cifrado round-trip, cifrado falla con clave incorrecta, mixin timestamps automáticos en `create`/`update`, AAD de tenant bloquea cross-tenant reuse.
- Convenciones: política de repositorio documentada (`backend/app/repositories/README.md`) explicando que **toda** query DEBE pasar por el repository base o uno que lo herede, y que un query SQLAlchemy directo fuera de `repositories/` es un bug de review.

## Capabilities

### New Capabilities

- `tenancy-foundation`: modelo `Tenant`, mixin `TenantScopedMixin` con `tenant_id`/UUID/timestamps, índice `(tenant_id, id)`, helpers `get_current_tenant_id` y `TenantContext`. Cubre el requisito de raíz multi-tenant.
- `soft-delete`: contrato de soft delete transversal: columna `deleted_at`, query helper que filtra filas activas, métodos `soft_delete()` y `restore()` en el repository base. Garantiza no-borrado físico.
- `pii-encryption`: helper de cifrado en reposo AES-256-GCM con AAD por tenant, `Settings.ENCRYPTION_KEY` validada en startup, API que no expone texto plano. Cubre el requisito de cifrado de PII (CBU, DNI, CUIL, email) que aplicarán módulos posteriores.
- `repository-base`: `TenantScopedRepository[T]` genérico con scope de tenant y soft delete activos por defecto; punto único por donde pasan las queries. Cualquier query fuera del repository base es un defecto de revisión.
- `alembic-setup`: configuración Alembic async, convención de nombres, script template, y migración inicial `001_tenant` que crea la tabla `tenant`.

### Modified Capabilities

Ninguna. C-02 introduce primitivas; todavía no hay specs vigentes que cambien (las de `C-01` describen scaffolding y conexión; no se modifican sus requirements).

## Impact

- **Código nuevo**:
  - `backend/app/models/tenant.py` (modelo ORM `Tenant`).
  - `backend/app/models/mixins.py` (`TenantScopedMixin`, `SoftDeleteMixin`).
  - `backend/app/core/security/crypto.py` (AES-256-GCM).
  - `backend/app/core/tenancy.py` (resolución de tenant, contexto).
  - `backend/app/core/config.py` (extender `Settings` con `ENCRYPTION_KEY`).
  - `backend/app/repositories/base.py` (`TenantScopedRepository`).
  - `backend/app/repositories/__init__.py` y `backend/app/repositories/README.md`.
  - `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/script.py.mako`, `backend/alembic/versions/001_tenant.py`.
- **APIs**: ninguna ruta HTTP nueva. C-02 no expone endpoints; el contrato HTTP vive en changes posteriores (C-03 auth, C-04 RBAC).
- **Dependencias**: se confirma uso de `cryptography` (AES-GCM) en `pyproject.toml`; el resto ya está en C-01.
- **Tests nuevos**:
  - `backend/tests/unit/test_crypto.py` (round-trip, AAD cross-tenant, clave incorrecta, IV aleatorio, no-log).
  - `backend/tests/unit/test_mixins.py` (timestamps automáticos, soft delete, restore).
  - `backend/tests/integration/test_tenant_isolation.py` (tenant A no lee/escribe datos de tenant B).
  - `backend/tests/integration/test_soft_delete_repository.py` (`list` no muestra eliminados, `count` no cuenta eliminados, `*_unsafe_*` sí los ve).
  - `backend/tests/integration/test_alembic_migration_001.py` (migration up/down aplica, índices y constraints correctos).
- **Migraciones Alembic**: una sola (`001_tenant`). Cambios de schema futuros = una migración por change.
- **Reglas duras que se activan desde C-02**:
  - Regla 8 (identidad desde JWT) se materializa con el `TenantContext` resuelto en `core/tenancy.py`; su contrato se respeta desde aquí aunque la verificación JWT llegue en C-03.
  - Regla 9 (multi-tenancy row-level): el repository base hace cumplir el filtro por `tenant_id` en cada query.
  - Regla 12 (AES-256 para PII): helper disponible, uso obligatorio desde C-07 en adelante.
  - Regla 13 (soft delete): mixin + repository base lo garantizan.
  - Regla 14 (identidad por UUID interno): el mixin usa `UUID` como PK de toda entidad.
- **No se toca** (fuera de scope): auth (C-03), RBAC (C-04), audit log (C-05), entidades académicas (C-06+), frontend (C-21+).
