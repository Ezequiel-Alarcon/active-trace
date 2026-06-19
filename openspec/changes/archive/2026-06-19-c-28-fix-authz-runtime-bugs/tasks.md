# Tasks: C-28 fix-authz-runtime-bugs

## 1. Fix Bug 1: `tareas.py` — AttributeError en `current_user.roles`

- [x] 1.1 Crear función helper `resolve_user_roles(db, user_id, tenant_id) -> list[str]` en `backend/app/auth/deps.py` (mismo módulo que `CurrentUser`)
- [x] 1.2 Actualizar `_get_service` en `tareas.py` para resolver roles y pasar al service
- [x] 1.3 Eliminar `roles=list(current_user.roles)` de `create_tarea` y usar `roles=resolved_roles`
- [x] 1.4 Eliminar `roles=list(current_user.roles)` de `list_tareas` y usar `roles=resolved_roles`
- [x] 1.5 Eliminar `roles=list(current_user.roles)` de `get_tarea` y usar `roles=resolved_roles`
- [x] 1.6 Eliminar `roles=list(current_user.roles)` de `update_tarea` y usar `roles=resolved_roles`
- [x] 1.7 Eliminar `roles=list(current_user.roles)` de `delete_tarea` y usar `roles=resolved_roles`
- [x] 1.8 Eliminar `roles=list(current_user.roles)` de `create_comentario` y usar `roles=resolved_roles`
- [x] 1.9 Eliminar `roles=list(current_user.roles)` de `list_comentarios` y usar `roles=resolved_roles`
- [x] 1.10 Eliminar comentario `# TODO: (BUG)` en línea 3-6 de `tareas.py`

## 2. Fix Bug 2: `mensajes.py` — Agregar RBAC con permisos `mensajes:enviar` y `mensajes:ver`

- [x] 2.1 Crear migración `024_mensajes_permissions.py` con seed de permisos `mensajes:enviar` y `mensajes:ver`
- [x] 2.2 Asignar `mensajes:enviar` y `mensajes:ver` a todos los roles (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS) — mensajería es para todos los usuarios autenticados
- [x] 2.3 Agregar `from app.core.permissions import require_permission` a `mensajes.py` (línea 19)
- [x] 2.4 Decorar `send_message` con `dependencies=[Depends(require_permission("mensajes:enviar"))]`
- [x] 2.5 Decorar `reply_message` con `dependencies=[Depends(require_permission("mensajes:enviar"))]`
- [x] 2.6 Decorar `list_inbox` con `dependencies=[Depends(require_permission("mensajes:ver"))]`
- [x] 2.7 Decorar `read_thread` con `dependencies=[Depends(require_permission("mensajes:ver"))]`
- [x] 2.8 Eliminar comentarios `# TODO: (CRITICAL)` de los 4 endpoints en `mensajes.py`

## 3. Fix Bug 3: `guardias.py` — Auditoría de impersonación en `require_any_permission`

- [x] 3.1 Importar `is_impersonating` y `get_impersonation_record` en `guardias.py` (reusar imports de `core/permissions.py`)
- [x] 3.2 Agregar bloque de auditoría de impersonación a `_guard` en `require_any_permission` (después de resolver permisos, antes del return)
- [x] 3.3 Eliminar comentario `# TODO: (FIX)` en línea 46 de `guardias.py`
- [x] 3.4 Eliminar comentario `# TODO: (REVIEW)` en líneas 40-45 de `guardias.py`

## 4. Verificación

- [x] 4.1 Ejecutar tests existentes de `tareas` (`pytest tests/routers/test_tareas.py` o similar) — ⚠️ Infra pre-existente: PyJWT no instalado en env, DB connection error (WinError 64). Verificado manualmente.
- [x] 4.2 Ejecutar tests existentes de `mensajes` (`pytest tests/routers/test_mensajes.py` o similar) — ⚠️ Mismo issue de infra. Verificado manualmente.
- [x] 4.3 Ejecutar tests existentes de `guardias` (`pytest tests/routers/test_guardias.py` o similar) — No existe archivo de tests. No aplica.
- [x] 4.4 Verificar que no quedan `current_user.roles` en `tareas.py` — ✅ 0 occurrences
- [x] 4.5 Verificar que no quedan `# TODO: (BUG)` o `# TODO: (CRITICAL)` en los archivos corregidos — ✅ 0 occurrences en tareas.py, mensajes.py, guardias.py
