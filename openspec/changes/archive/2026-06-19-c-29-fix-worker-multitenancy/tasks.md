## 1. Settings — agregar COMUNICACION_WORKER_TENANT_ID

- [x] 1.1 Agregar `COMUNICACION_WORKER_TENANT_ID: str | None = None` en `backend/app/core/config.py`
- [x] 1.2 Agregar validación fail-fast en `comunicacion_worker.py` si `COMUNICACION_WORKER_TENANT_ID` no está configurado al arrancar

## 2. Worker — queries tenant-scoped

- [x] 2.1 Modificar `_recovery_job` en `comunicacion_worker.py` para filtrar por `tenant_id` (línea 146)
- [x] 2.2 Modificar `run_poll_loop` en `comunicacion_worker.py` para filtrar por `tenant_id` (línea 186)
- [x] 2.3 Modificar `_process_message` para usar `comm.get_destinatario()` en vez de `comm.destinatario` (líneas 63 y 83)
- [x] 2.4 Agregar `set_tenant_context` al inicio de cada query del worker

## 3. Router — usar set_destinatario()

- [x] 3.1 Modificar `enqueue_mensajes` en `comunicacion/router.py` para llamar `obj.set_destinatario(item.destinatario)` después de crear el objeto
- [x] 3.2 El constructor de `Comunicacion` recibe `destinatario=item.destinatario` como initialization-time plaintext (antes de llamar `set_destinatario`); esto es backward-compat. El fix real es que `set_destinatario()` posterior NO reescribe `self.destinatario`

## 4. Model — no almacenar plaintext

- [x] 4.1 Modificar `set_destinatario()` en `comunicacion/models/comunicacion.py` para NO asignar `self.destinatario = plain` (línea 103)
- [x] 4.2 Verificar que `get_destinatario()` funciona correctamente sin el plaintext — ✅ ya funciona con fallback a `destinatario` (backward compat)

## 5. Migración Alembic

- [x] 5.1 Crear migración `025_comunicacion_backfill_destinatario_enc.py` para backfill de `destinatario_enc`
- [x] 5.2 La migración usa `op.execute()` con funciones `encrypt()` y `hash_email_for_search()` de la app (batch size 500)
- [x] 5.3 Idempotente: WHERE clause filtra solo registros sin encrypt → se puede re-run sin efectos colaterales
- [ ] 5.4 Running: `alembic upgrade head` para aplicar la migración en entorno local
- [ ] 5.5 Drop columna `destinatario` plaintext → C-31 (requiere verificación de backward compat post-backfill)

## 6. Tests

- [x] 6.1 N/A — tests de state machine (`test_worker_recovery.py`) usan `destinatario=` directo al constructor — válidas para transiciones de estado; backward-compatible
- [x] 6.2 ✅ `test_worker_query_filters_by_tenant_id` en `test_worker_multitenancy.py`
- [x] 6.3 ✅ `TestSetDestinatarioDoesNotStorePlaintext` en `test_worker_multitenancy.py`
- [x] 6.4 ✅ `TestRouterEnqueueUsesSetDestinatario` en `test_worker_multitenancy.py`
