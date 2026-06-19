## Why

Dos bugs criticos rompen producción en backend:

1. **AttributeError en runtime** (`tareas.py`): 7 endpoints usan `current_user.roles` pero `CurrentUser` (auth/deps.py) solo tiene `user_id`, `tenant_id`, `session_id`, `is_2fa_verified`, `totp_enabled`. Cualquier usuario que intente crear/listar/actualizar/eliminar tareas recibe un `AttributeError`.

2. **RBAC ausente** (`mensajes.py`): Los 4 endpoints (`send_message`, `reply_message`, `list_inbox`, `read_thread`) solo tienen autenticación (`get_current_user`) pero carecen de autorización (`require_permission`). Cualquier usuario autenticado puede leer y enviar mensajes de cualquier otro usuario del tenant.

Ambos bugs son CRÍTICOS porque afectan la seguridad (acceso no autorizado a mensajes) y la disponibilidad (crash en tareas).

## What Changes

### Bug Fix 1: `tareas.py` — Eliminar uso de `current_user.roles`

- Reemplazar `roles=list(current_user.roles)` (atributo inexistente) por llamada al helper `resolve_user_roles(db, user_id, tenant_id)` en 7 endpoints: `create_tarea`, `list_tareas`, `get_tarea`, `update_tarea`, `delete_tarea`, `create_comentario`, `list_comentarios`.
- El helper `resolve_user_roles()` se creó en `auth/deps.py` (mismo módulo que `CurrentUser`).
- **Nota**: NO se eliminó el parámetro `roles` del service porque `TareaService` lo usa internamente en `_es_admin()` y `_verificar_acceso()` para control de acceso. Mantener el parámetro fue la decisión correcta.

### Bug Fix 2: `mensajes.py` — Agregar RBAC

- Agregar permisos `mensajes:enviar` y `mensajes:ver` al catálogo de permisos (seed)
- Decorar `send_message` y `reply_message` con `dependencies=[Depends(require_permission("mensajes:enviar"))]`
- Decorar `list_inbox` y `read_thread` con `dependencies=[Depends(require_permission("mensajes:ver"))]`

### Bug Fix 3: `guardias.py` — Auditoría de impersonación en `require_any_permission`

- Agregar a `require_any_permission` el mismo bloque de auditoría de impersonación que tiene `require_permission` en `core/permissions.py`:
  - `is_impersonating` check
  - `request.state.impersonating` y `request.state.impersonated_user_id`

## Capabilities

### New Capabilities

- `mensajeria-interna-rbac`: Control de acceso basado en permisos para mensajería interna (`mensajes:enviar`, `mensajes:ver`). Requisitos ya definidos en spec `mensajeria-interna` (C-20 archivado) pero sin enforcement RBAC — esta capability lo agrega.

### Modified Capabilities

- `tareas-crud`: Requirement "Create tarea", "Read tarea", "Update tarea estado", "Soft-delete tarea" ya tienen `require_permission("tareas:gestionar")` declarado en los endpoints. El bug era que la implementación intentaba usar `current_user.roles` (atributo inexistente en `CurrentUser`). Fix: helper `resolve_user_roles()` en `auth/deps.py` que delega a `PermissionResolver`. Sin cambio de requisitos.

- `guardias-crud`: Requirement `require_any_permission` en `list_guardias` funciona pero noPopula el estado de impersonación. Fix de seguridad, sin cambio de requisitos.

## Impact

### Archivos afectados

| Archivo | Cambio |
|---------|--------|
| `backend/app/auth/deps.py` | **NUEVO**: helper `resolve_user_roles(db, user_id, tenant_id)` |
| `backend/app/routers/tareas.py` | Reemplazar `current_user.roles` por `resolve_user_roles()` en 7 endpoints |
| `backend/app/routers/mensajes.py` | Agregar `dependencies=[Depends(require_permission(...))]` a 4 endpoints |
| `backend/app/routers/guardias.py` | Agregar auditoría de impersonación a `require_any_permission` |
| `backend/alembic/versions/024_mensajes_permissions.py` | **NUEVA**: seed de permisos `mensajes:enviar` y `mensajes:ver` |

### Permisos a seedear

- `mensajes:enviar` — enviar y responder mensajes
- `mensajes:ver` — listar inbox y leer hilos

### Dependencias verificadas

- C-04 (RBAC) — archivado, `require_permission` y `PermissionResolver` ya existen
- C-20 (mensajeria-interna) — archivado, endpoints y service ya existen
