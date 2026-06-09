## 1. Settings y dependencias

- [x] 1.1 Agregar `cryptography>=43` a `backend/pyproject.toml` y refrescar el lock.
- [x] 1.2 Extender `backend/app/core/config.py` con `ENCRYPTION_KEY: SecretStr` y un validador que exija exactamente 32 bytes; fail-fast en `Settings()`.
- [x] 1.3 Agregar `KEY_REGISTRY: dict[int, bytes] = {1: ENCRYPTION_KEY.get_secret_value().encode()}` y `CURRENT_KEY_ID: int = 1` en `config.py` para soportar rotación futura.
- [x] 1.4 Documentar `ENCRYPTION_KEY` en `backend/.env.example` con un valor de placeholder de 32 bytes y nota de generación (`python -c "import secrets; print(secrets.token_urlsafe(32))"`).
- [x] 1.5 Verificar `.gitignore` ignora `.env*` salvo `.env.example`; añadir un test que lo asegura.

## 2. Cifrado AES-256-GCM (PII)

- [x] 2.1 Crear `backend/app/core/security/__init__.py` y `backend/app/core/security/crypto.py` con las funciones `encrypt`, `decrypt`, `encrypt_bytes`, `decrypt_bytes` y una constante `NONCE_SIZE = 12` y `TAG_SIZE = 16`.
- [x] 2.2 Implementar `encrypt(plaintext: str, *, tenant_id: UUID, aad_suffix: str | None = None, key_id: int = 1) -> str` y su par `decrypt`. Formato del blob: `version(1) || key_id(1) || nonce(12) || tag(16) || ciphertext`, base64.
- [x] 2.3 Implementar `encrypt_bytes` / `decrypt_bytes` con la misma estructura binaria (sin base64).
- [x] 2.4 Derivar AAD como `f"{tenant_id}:{aad_suffix}"` cuando `aad_suffix` está presente, o `str(tenant_id)` cuando no lo está.
- [x] 2.5 Configurar el logger `activia_trace.security.crypto` para que solo registre outcome (`encrypted`/`decrypted`/`failed`), `tenant_id`, `aad_suffix` y un código de error opaco — nunca plaintext, nunca ciphertext, nunca AAD completo.
- [x] 2.6 Escribir `backend/tests/unit/test_crypto.py` con los casos: round-trip OK, IV aleatorio (mismo plaintext → 2 ciphertexts distintos), tamper detection (1 bit flip → falla), AAD tenant mismatch → falla, AAD suffix mismatch → falla, clave de 31/33 bytes → falla al instanciar settings, helper no loggea plaintext en un test que captura `caplog`.

## 3. Tenancy: modelo, mixin, contexto

- [x] 3.1 Crear `backend/app/models/__init__.py` que expone `Base` (declarative base de SQLAlchemy 2.0) y registra los mixins y modelos.
- [x] 3.2 Crear `backend/app/models/mixins.py` con `TenantScopedMixin` y `SoftDeleteMixin`. `TenantScopedMixin` declara `id`, `tenant_id` (FK `tenant.id` ON DELETE RESTRICT), `created_at`, `updated_at`, `deleted_at` y los índices `ix_<tabla>_tenant` y `ix_<tabla>_tenant_deleted`. Usar `sqlalchemy.dialects.postgresql.UUID` (no `String`).
- [x] 3.3 Crear `backend/app/models/tenant.py` con `class Tenant(Base, SoftDeleteMixin):` que NO hereda de `TenantScopedMixin` (es la raíz). Columnas: `id` (UUID PK), `codigo` (str, unique), `nombre` (str), `estado` (Enum `TenantEstado.activo | inactivo`), `created_at`, `updated_at`, `deleted_at`. Constraint `ck_tenant_estado`.
- [x] 3.4 Crear `backend/app/core/tenancy.py` con `TenantContext` (dataclass: `tenant_id: UUID`, `is_impersonating: bool = False`), `set_tenant_context(ctx)`, `reset_tenant_context()`, `get_current_tenant_id() -> UUID` (raise si no hay contexto), `get_current_tenant_context() -> TenantContext`.
- [x] 3.5 Crear `backend/app/core/dependencies.py` con `tenant_context_dep(x_tenant_id: UUID | None = Header(default=None, alias="X-Tenant-Id")) -> TenantContext` — placeholder de C-02; C-03 lo reemplaza por el resolver de JWT. En producción fuera de tests, `X-Tenant-Id` debe ser ignorado cuando hay un contexto de sesión válido; para C-02 basta con requerir header en el path de tests.
- [x] 3.6 Escribir `backend/tests/unit/test_mixins.py`: timestamps se setean en INSERT, `updated_at` se refresca en UPDATE, `tenant_id` NOT NULL falla, FK a `tenant.id` falla si no existe.
- [x] 3.7 Escribir `backend/tests/unit/test_tenant_context.py`: `get_current_tenant_id()` fuera de contexto → raise; `set_tenant_context` + lectura → OK; contextos concurrentes en distintas tasks no se pisan (test con `asyncio.gather`).

## 4. Soft delete transversal

- [x] 4.1 Implementar `soft_delete(obj)` y `restore(obj)` en el repository base (ver §5).
- [x] 4.2 Implementar la seam `audit_emit(action: str, *, entity: str | None = None, entity_id: UUID | None = None, tenant_id: UUID | None = None, **extra)` en `backend/app/core/audit.py` — wrapper sobre `logger.warning("audit", extra=...)` con un set fijo de action codes (`ROW_SOFT_DELETE`, `ROW_RESTORE`, `TENANT_CROSS_QUERY`, `ROW_INCLUDE_DELETED`, `ROW_HARD_DELETE`).
- [x] 4.3 Documentar en `backend/app/core/audit.py` que C-05 reemplazará el wrapper por escritura a `AuditLog`; el seam queda estable.
- [x] 4.4 Cubrir con tests que `soft_delete` setea `deleted_at`, `restore` lo limpia, `list`/`count` no cuentan filas soft-deleted, y que cada llamada emite un audit con el action code correcto.

## 5. Repository base tenant-scoped

- [x] 5.1 Crear `backend/app/repositories/__init__.py` y `backend/app/repositories/base.py` con `class TenantScopedRepository(Generic[T], ABC)` (o `Generic[T]` con `__init__` que valida) que recibe `session: AsyncSession`, `model: type[T]` y `tenant_id: UUID`. Constructor raise si `tenant_id is None`.
- [x] 5.2 Implementar `get_by_id`, `list`, `create`, `update`, `soft_delete`, `restore`, `count` con el filtro `WHERE tenant_id = :t AND deleted_at IS NULL` por defecto. `create` rechaza `tenant_id` distinto al del repo.
- [x] 5.3 Implementar `unsafe_get`, `unsafe_list_all` (incluye soft-deleted), `unsafe_count`, `unsafe_soft_delete`, `unsafe_restore`, `unsafe_physical_delete` (solo para `unsafe_physical_delete`: `await session.delete(obj)`). Cada uno llama a `audit_emit(...)` con su action code.
- [x] 5.4 Crear `get_tenant_repository(model, session) -> TenantScopedRepository` factory que lee `get_current_tenant_id()` y construye el repo.
- [x] 5.5 Crear `backend/app/repositories/README.md` con la política: (a) toda query pasa por acá, (b) `unsafe_*` requiere PR con justificación, (c) servicios NUNCA reciben `AsyncSession` cruda.
- [x] 5.6 Crear `backend/tests/_fakes/models.py` con un `class Smoke(Base, TenantScopedMixin)` que sirve de conejo de Indias para tests de integración (nombre no persistido en producción). Documentar en el módulo que es solo para tests.
- [x] 5.7 Escribir `backend/tests/integration/test_repository_base.py`: construcción requiere tenant; `get_by_id` con id de otro tenant → None; `list` no muestra soft-deleted; `count` no cuenta soft-deleted; `create` con tenant_id mismatch → raise; `update` no cambia tenant_id; `restore` revierte `soft_delete`; `unsafe_list_all` muestra todo + audit; `unsafe_physical_delete` borra + audit.

## 6. Aislamiento multi-tenant (test obligatorio)

- [x] 6.1 Escribir `backend/tests/integration/test_tenant_isolation.py` con DB real: sembrar tenant A y tenant B con datos en `Smoke` para cada uno. Verificar que el repository de A nunca lee ni escribe datos de B en ninguna combinación de métodos.
- [x] 6.2 Verificar explícitamente: (a) `get_by_id` con id de B desde A → None, (b) `list` de A no contiene filas de B, (c) `count` de A no cuenta B, (d) `create` con `tenant_id=B` desde A → raise, (e) `update`/`soft_delete` sobre id de B desde A → no afecta la fila, (f) tests corren concurrentes (`asyncio.gather`) sin leakage.
- [x] 6.3 Cubrir con tests que un `TenantContext` incorrecto no puede filtrar a otros repos del mismo request (test con dos repos en el mismo handler apuntando a tenants distintos).

## 7. Alembic: configuración y migración 001

- [x] 7.1 Inicializar Alembic en `backend/`: `alembic init -t async alembic`. Adaptar `alembic.ini` para que NO tenga `sqlalchemy.url` (lo lee de `Settings`).
- [x] 7.2 Reescribir `alembic/env.py` para usar `async_engine_from_config` y `connection.run_sync(do_run_migrations)` con `asyncio.run`. Importar `Base` desde `app.models` y `Settings` desde `app.core.config`.
- [x] 7.3 Crear `alembic/script.py.mako` con un bloque de comentario al inicio recordando la convención de nombres y el requisito de `TenantScopedMixin` para tablas de dominio.
- [x] 7.4 Crear `backend/alembic/versions/001_tenant.py`: `upgrade()` crea tabla `tenant` con columnas, índices (`ux_tenant_codigo`, `ix_tenant_created_at`, `ix_tenant_deleted_at`), y constraint `ck_tenant_estado`. `downgrade()` drop completo.
- [x] 7.5 Verificar convención de nombres: `op.create_index(..., name=...)` debe seguir `ix_<tabla>_<col>` o `ux_<tabla>_<col>`. Si un nombre no cumple, el lint Ruff custom (configurar en `pyproject.toml` bajo `[tool.ruff.lint.custom]`) lo rechaza.
- [x] 7.6 Escribir `backend/tests/integration/test_alembic_migration_001.py`: aplica y revierte la migración contra una DB real, valida que la tabla existe con las columnas y los índices correctos tras `upgrade`, y que la tabla se elimina tras `downgrade`.
- [x] 7.7 Configurar `conftest.py` global con fixture `applied_migrations` (una sola vez por sesión) y `db_session` (transacción por test, rollback al final).

## 8. Documentación y política de revisión

- [x] 8.1 Crear `backend/app/repositories/README.md` (ver 5.5).
- [x] 8.2 Agregar a `docs/ARQUITECTURA.md` §6 una nota "Implementación: `app/core/tenancy.py` + `app/repositories/base.py` (C-02)" como puntero al código.
- [x] 8.3 Crear `backend/docs/decisiones/adr-007-key-rotation.md` (placeholder) con la decisión D4 sobre el seam de rotación.
- [x] 8.4 Actualizar `CHANGES.md` con check `[x]` en C-02 cuando se archive el change.

## 9. Verificación final

- [x] 9.1 Correr `pytest` completo: todos los tests verdes, cobertura ≥80% global, ≥90% en `app/core/security/crypto.py`, `app/repositories/base.py`, `app/core/tenancy.py`, `app/models/mixins.py`, `app/models/tenant.py`.
- [x] 9.2 Correr `ruff check backend/`, `ruff format --check backend/`, `mypy backend/app` sin errores.
- [x] 9.3 Levantar la app con `uvicorn app.main:app --reload` y verificar `GET /health` responde 200; opcional `GET /health/tenant?X-Tenant-Id=...` (placeholder de C-02) responde 200 cuando el header es un UUID válido.
- [x] 9.4 Correr `alembic upgrade head` contra la DB de dev y `alembic downgrade base` para confirmar reversibilidad; volver a `upgrade head`.
- [x] 9.5 Ejecutar `openspec verify core-models-y-tenancy` (cuando el comando esté disponible) y resolver cualquier gap entre specs y código.
