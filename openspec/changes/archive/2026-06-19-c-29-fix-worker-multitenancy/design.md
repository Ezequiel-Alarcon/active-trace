## Context

El worker de comunicaciones (`comunicacion_worker.py`) fue introducido en C-12 y corre como proceso Python independiente via `asyncio.run(run_worker())`. Carece de contexto HTTP/JWT, lo que significa que no tiene forma directa de saber qué tenant procesar. Los queries en `_recovery_job` y `run_poll_loop` no filtran por `tenant_id`, violando el aislamiento multi-tenant.

Además, el modelo `Comunicacion` mantiene coexistencia de `destinatario` (plaintext) y `destinatario_enc` (cifrado), cuando la KB E21 y el spec `pii-encryption` exigen que `destinatario` sea cifrado exclusivamente.

## Goals / Non-Goals

**Goals:**
- Quebrar definitivamente el bug de multi-tenancy en el worker: todos los queries deben filtrar por `tenant_id`
- Eliminar el almacenamiento de `destinatario` en plaintext, migrando completamente a `destinatario_enc`/`destinatario_hash`
- Asegurar que el router de comunicación use `set_destinatario()` en vez de asignación directa

**Non-Goals:**
- No se modifica el diseño de cola o estados de comunicación
- No se introduce multi-tenancy cross-tenant (el worker opera en un tenant a la vez)
- No se cambia el mecanismo de dispatch (webhook/noop)

## Decisions

### Decisión 1: Arquitectura del worker — tenant-aware via configuración

**Opción A (elegida)**: Un worker por tenant, configurado via `COMUNICACION_WORKER_TENANT_ID`. Cada запуска del worker场内 solo un `tenant_id`. Esto es simple, seguro y alineado con el principio de mínimo privilegio.

**Opción B**: Worker tenant-agnostic que recibe `tenant_id` por mensaje de la cola. Descartada: introduce complejidad de handshake y no escala.

**Opción C**: Scopear dinámicamente por sesión basada en el primer mensaje recibido. Descartada: violaría el aislamiento en el borde del primer mensaje.

**Implementación**:
- Agregar `COMUNICACION_WORKER_TENANT_ID: str | None = None` en `settings`
- Si está configurado, el worker llama `set_tenant_context(TenantContext(tenant_id=valor))` antes de cada query
- Si no está configurado, el worker fallaría al arrancar (fail-fast en vez de procesar todos los tenants)

### Decisión 2: Queries del worker con filtrado por tenant

**Para `_recovery_job`**: Agregar `where(Comunicacion.tenant_id == tenant_id)` al statement (línea ~146).

**Para `run_poll_loop`**: Agregar `where(Comunicacion.tenant_id == tenant_id)` al statement de poll (línea ~186).

El `tenant_id` viene de `get_settings().COMUNICACION_WORKER_TENANT_ID`.

### Decisión 3: Migración del modelo `Comunicacion`

**Estado actual**: Convivencia de `destinatario` (plaintext), `destinatario_hash` y `destinatario_enc`.

**Estado objetivo (C-29)**: Dejar de escribir plaintext via `set_destinatario()`, hacer backfill de datos existentes. La columna plaintext `destinatario` permanece durante la migración para backward-compat.

**Estado objetivo (C-31)**: Eliminar columna `destinatario` del todo.

**Pasos en C-29**:
1. Modificar `set_destinatario()` para NO asignar `self.destinatario = plain`
2. `get_destinatario()` ya funciona correctamente (retorna decrypted si existe `destinatario_enc`, con fallback a plaintext para backward-compat)
3. Migración Alembic 025: backfill `destinatario_enc` y `destinatario_hash` para todos los registros existentes

**Pasos en C-31** (deferred):
- Drop columna `destinatario` (una vez verificado que `get_destinatario()` no necesita el fallback)
- Actualizar modelo: `destinatario_enc` → `destinatario`, mantener `destinatario_hash`

### Decisión 4: Router — usar `set_destinatario()`

En `enqueue_mensajes` (línea 89), reemplazar:
```python
destinatario=item.destinatario,  # BUG: almacena plaintext
```
Por:
```python
# Crear objeto sin destinatario, luego llamar set_destinatario
obj = Comunicacion(...)
obj.set_destinatario(item.destinatario)
```

Esto debe hacerse DESPUÉS de crear el objeto porque `set_destinatario` necesita `self.tenant_id` que se asigna en el constructor.

## Risks / Trade-offs

[Risk] Worker configurado sin `COMUNICACION_WORKER_TENANT_ID` → Mitigation: fail-fast al arrancar con mensaje claro

[Risk] Datos existentes sin backfill tienen `destinatario_enc` vacío → Mitigation: migración 025 backfill it in batches; `get_destinatario()` cae back a plaintext como safety net

[Risk] Backward-compat fallback en `get_destinatario()` puede enmascarar registros sin encrypt → Mitigation: C-31 elimina la columna plaintext una vez verificado

## Migration Plan

1. **Fase 1 (C-29 — este change)**:
   - Agregar `COMUNICACION_WORKER_TENANT_ID` a settings con valor requerido
   - Modificar `_recovery_job` y `run_poll_loop` para filtrar por `tenant_id`
   - Modificar `_process_message` para usar `comm.get_destinatario()`
   - Modificar router para usar `set_destinatario()`
   - Modificar `set_destinatario()` para NO escribir plaintext
   - Crear y aplicar migración Alembic 025: backfill `destinatario_enc` y `destinatario_hash` para registros existentes

2. **Fase 2 (C-31)**:
   - Verificar que todos los registros tienen `destinatario_enc` populated
   - Drop columna `destinatario`
   - Actualizar modelo: `destinatario_enc` → `destinatario`, mantener `destinatario_hash`

3. **Rollback**: Revertir migración Alembic 025, pero los bugs de tenancy ya quedan fijos.

## Open Questions

- **Q1**: ¿Cómo se gestionan los workers existentes? ¿Se necesita un script de migración de configuración por tenant? → Cada tenant corre su propio worker con su `COMUNICACION_WORKER_TENANT_ID`. Operationally simple.
- **Q2**: ¿Hay tests en C-12 que validaban el worker sin tenant y que necesitan actualizarse? → **RESUELTO**: los tests existentes de state machine (`test_worker_recovery.py`) usan `destinatario=` directo al constructor — son backward-compatible con el modelo actual que conserva la columna plaintext.
