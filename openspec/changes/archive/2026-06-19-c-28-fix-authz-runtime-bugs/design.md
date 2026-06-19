## Context

Dos bugs críticos en producción que comprometen seguridad y disponibilidad:

1. **Bug 1 (`tareas.py`)**: 8 líneas usan `current_user.roles` pero `CurrentUser` (auth/deps.py:38) solo tiene `user_id`, `tenant_id`, `session_id`, `is_2fa_verified`, `totp_enabled`. Esto causa `AttributeError` en runtime cuando cualquier usuario interactúa con tareas. Los endpoints YA tienen `require_permission("tareas:gestionar")` declarado; el bug es que el código intenta acceder a un atributo inexistente.

2. **Bug 2 (`mensajes.py`)**: 4 endpoints (`send_message`, `reply_message`, `list_inbox`, `read_thread`) solo usan `get_current_user` (autenticación) pero carecen de `require_permission` (autorización). Cualquier usuario autenticado puede leer/enviar mensajes de cualquier otro usuario del tenant.

3. **Bug 3 (`guardias.py`)**: `require_any_permission` no incluye el bloque de auditoría de impersonación que sí tiene `require_permission` estándar en `core/permissions.py:44-51`. Esto significa que cuando un ADMIN impersona a un usuario y accede a guardias, la auditoría no registra la impersonación.

## Goals / Non-Goals

**Goals:**
- Corregir el `AttributeError` en `tareas.py` eliminando el uso de `current_user.roles`
- Agregar RBAC a los 4 endpoints de `mensajes.py` con permisos `mensajes:enviar` y `mensajes:ver`
- Agregar auditoría de impersonación a `require_any_permission` en `guardias.py`
- Mantener compatibilidad: los endpoints con `require_permission` ya existente siguen funcionando igual

**Non-Goals:**
- No modificar la lógica de negocio de los servicios (`TareaService`, `MensajeService`)
- No eliminar el parámetro `roles` de `TareaService` — se usa internamente en `_es_admin()` y `_verificar_acceso()`
- No agregar nuevos endpoints ni modificar rutas existentes

## Decisions

### Decision 1: Cómo resolver `current_user.roles` en `tareas.py`

**Opción A**: Reemplazar `current_user.roles` con `PermissionResolver.resolve(current_user.user_id, current_user.tenant_id)`

- ✅ Permite mantener la firma actual del service (que recibe `roles`)
- ✅ Consistente con el patrón RBAC existente
- ❌ Añade un query adicional a la DB en cada request (aunque PermissionResolver tiene cache)
- ❌ Los endpoints ya verifican `tareas:gestionar` via `require_permission` — los `roles` en el service son redundantes

**Opción B**: Eliminar el parámetro `roles` de los métodos del service

- ✅ Elimina código muerto y query redundante
- ✅ Simplifica la interfaz
- ⚠️ Requiere verificar que el service no use internamente `roles` para lógica de negocio

**Decisión**: Opción A (con helper). Se crea `resolve_user_roles()` en `auth/deps.py` que delega a `PermissionResolver.resolve()`. Se mantienen las firmas de los métodos del service con `roles` porque `TareaService` lo usa internamente en `_es_admin()` y `_verificar_acceso()`. Opción B (eliminar `roles`) fue descartada tras verificar que el parámetro es necesario para la lógica de autorización.

### Decision 2: Permisos para mensajería

**Opción A**: Reutilizar permisos existentes (`tareas:gestionar`, etc.)

- ❌ Viola el principio de menor privilegio
- ❌ Mezcla dominios de negocio

**Opción B**: Crear permisos específicos `mensajes:enviar` y `mensajes:ver`

- ✅ Separa Concerns por dominio
- ✅ Consistente con el catálogo existente (`avisos:publicar`, `avisos:confirmar`)
- ⚠️ Requiere seedear los permisos

**Decisión**: Opción B. Los permisos `mensajes:enviar` y `mensajes:ver` se seedearán en la migración existente más reciente (o en una nueva si no hay migración activa).

### Decision 3: Auditoría de impersonación en `require_any_permission`

**Problema**: `require_any_permission` (guardias.py:35) no populates `request.state.impersonating` ni `request.state.impersonated_user_id`.

**Solución**: Agregar el mismo bloque que tiene `require_permission` en `core/permissions.py:44-51`:
```python
impersonating = is_impersonating(current_user.user_id)
request.state.impersonating = impersonating
if impersonating:
    record = get_impersonation_record(current_user.user_id)
    request.state.impersonated_user_id = record.target_user_id if record else None
else:
    request.state.impersonated_user_id = None
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Query adicional a la DB por cada request de tareas | `PermissionResolver` tiene cache en memoria; impacto mínimo |
| Los permisos `mensajes:enviar/ver` no existen en prod | Seed con `ON CONFLICT DO NOTHING` — idempotente |
| Tests existentes que mockean `current_user.roles` fallan | Ya no se usa `current_user.roles` — los mocks deben actualizarse a usar el helper |

## Migration Plan

1. **Deploy atómico**: todos los cambios se despliegan juntos en una sola migración + deploy de código.
   - Migración `024_mensajes_permissions.py` (seed de permisos)
   - Código: `auth/deps.py` (nuevo helper), `tareas.py`, `mensajes.py`, `guardias.py`

2. **Rollback**: reversible vía `alembic downgrade` + revert del código.

3. **Verificación post-deploy**:
   - `tareas.py`: crear/listar/actualizar/eliminar tareas sin `AttributeError`
   - `mensajes.py`: usuarios sin permiso reciben 403
   - `guardias.py`: logs de auditoría muestran impersonación correctamente

## Open Questions — RESOLVED

1. ~~¿El parámetro `roles` en `TareaService` se usa en algún lugar para lógica de negocio?~~ **RESUELTO**: SÍ se usa — en `_es_admin()` y `_verificar_acceso()`. Por eso se mantiene el parámetro y se crea el helper en `auth/deps.py`.

2. ~~¿Existe una migración activa donde agregar el seed de permisos?~~ **RESUELTO**: La última migración es `023_liquidaciones_honorarios.py`; se creó `024_mensajes_permissions.py` como nueva migración.
