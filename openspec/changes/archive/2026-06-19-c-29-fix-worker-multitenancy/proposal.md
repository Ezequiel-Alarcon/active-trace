## Why

El worker de comunicaciones (`comunicacion_worker.py`) y el router de comunicación (`comunicacion/router.py`) contienen violaciones críticas de seguridad: (1) los queries SQL no filtran por `tenant_id`, exponiendo datos de todos los tenants en entornos multi-tenant, y (2) el email del destinatario se almacena sin cifrar, violando los requisitos E21 de la KB y las reglas duras del proyecto.

Estos bugs fueron introducidos en C-12 (comunicaciones-cola-worker) y violan directamente:
- **Regla Dura #9**: `tenant_id` en cada tabla; los repositories filtran por tenant **por defecto**
- **Regla Dura #12**: Secretos y PII (CBU, DNI) **SIEMPRE AES-256**
- **KB E21**: `destinatario` de `Comunicacion` debe estar cifrado

## What Changes

- **Bug 1 (CRÍTICO)**: `comunicacion_worker.py` `_recovery_job` y `run_poll_loop` ejecutan queries `SELECT` sin filtrar por `tenant_id`. El worker corre como proceso separado y actualmente procesa mensajes de TODOS los tenants.
- **Bug 2**: `comunicacion_worker.py` usa `comm.destinatario` (plaintext) en lugar de `comm.get_destinatario()` (descifrado).
- **Bug 3** (corregido): `comunicacion/router.py` ya no asigna `destinatario=item.destinatario` directamente. Ahora usa `obj.set_destinatario(item.destinatario)` post-constructor.
- **Bug 4**: `models/comunicacion.py` mantiene `destinatario: Mapped[str]` en plaintext mientras coexiste con `destinatario_enc` y `destinatario_hash`.

> ⚠️ **Nota sobre Bug 4**: La columna plaintext `destinatario` NO se elimina en este change. El fix de Bug 4 implementa el stop-gap (`set_destinatario()` deja de escribir plaintext) y el backfill de datos existentes (migración 025). La eliminación definitiva de la columna plaintext (`DROP COLUMN destinatario`) se realiza en C-31, una vez verificada la backward-compatibilidad.

## Capabilities

### New Capabilities

- `worker-tenant-aware`: El worker de comunicaciones opera dentro de un `TenantContext` por запуска, ejecutando todos sus queries con `tenant_id` explícito. El worker recibe el `tenant_id` vía variable de entorno o configuración de startup. Queries: `_recovery_job`, `run_poll_loop`, y cualquier otro acceso a `Comunicacion`.

### Modified Capabilities

- `comunicacion-destinatario-cifrado` (from `pii-encryption`): El modelo `Comunicacion` debe migrar completamente a `destinatario_enc`/`destinatario_hash`, eliminando el campo plaintext `destinatario`. El router debe usar `obj.set_destinatario()` en lugar de asignación directa.

## Impact

- **Backend**: `backend/app/workers/comunicacion_worker.py`, `backend/app/modules/comunicacion/router.py`, `backend/app/modules/comunicacion/models/comunicacion.py`
- **Dependencias**: C-12 ( activo — introduce los bugs), C-02 (tenancy foundation)
- **Migración**: Alembic `025_comunicacion_backfill_destinatario_enc` para backfill de `destinatario_enc`/`destinatario_hash` sobre datos existentes. La migración `DROP COLUMN destinatario` se ejecuta en C-31.
- **Tests**: Tests existentes de C-12 que usaban `destinatario=` directo al constructor son backward-compatible con el modelo actual (usan la columna plaintext que aún existe).
