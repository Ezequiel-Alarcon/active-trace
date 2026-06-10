# usuario-crud Specification

## Purpose
TBD - created by archiving change usuarios-y-asignaciones. Update Purpose after archive.
## Requirements
### Requirement: Sistema SHALL exponer endpoint de creación de usuario protegido con `usuarios:gestionar`

El sistema SHALL exponer `POST /api/admin/usuarios` que acepta los campos del modelo `Usuario` (nombre, apellidos, email, dni, cuil, cbu, alias_cbu, banco, regional, legajo, legajo_profesional, fecha_nacimiento, genero, observaciones). El endpoint requiere permiso `usuarios:gestionar`. Los campos PII se cifran antes de persistir.

#### Scenario: ADMIN crea usuario exitosamente

- **WHEN** un usuario autenticado con rol ADMIN y tenant A envía `POST /api/admin/usuarios` con `{"nombre": "María", "apellidos": "García", "email": "maria@garcia.com"}`
- **THEN** el sistema crea el Usuario en tenant A con los campos PII cifrados
- **AND** retorna 201 con los datos del Usuario (campos PII descifrados en la respuesta)

#### Scenario: Usuario sin permiso recibe 403

- **WHEN** un usuario sin permiso `usuarios:gestionar` envía `POST /api/admin/usuarios`
- **THEN** el sistema retorna 403 Forbidden

#### Scenario: Email duplicado en el mismo tenant retorna 409

- **WHEN** existe un Usuario con email="maria@garcia.com" en tenant A
- **AND** se envía `POST /api/admin/usuarios` con email="maria@garcia.com" en tenant A
- **THEN** el sistema retorna 409 Conflict

#### Scenario: Creación con id existente de AuthUser vincula correctamente

- **WHEN** existe un `AuthUser` con id=X en tenant A
- **AND** se envía `POST /api/admin/usuarios` con `{"id": "X", "nombre": "María", ...}`
- **THEN** el sistema crea el Usuario con id=X (mismo UUID que AuthUser)
- **AND** la FK `usuario.id → auth_user.id` es válida

### Requirement: Sistema SHALL exponer endpoint de listado de usuarios con filtros

El sistema SHALL exponer `GET /api/admin/usuarios` que retorna la lista de usuarios del tenant activos (no soft-deleted). Debe soportar filtros opcionales por `estado` y `busqueda` (texto parcial en nombre o apellidos).

#### Scenario: Listar usuarios del tenant

- **WHEN** un ADMIN de tenant A hace `GET /api/admin/usuarios`
- **THEN** el sistema retorna todos los Usuarios activos de tenant A
- **AND** no incluye Usuarios de tenant B

#### Scenario: Listar usuarios con filtro de búsqueda

- **WHEN** un ADMIN hace `GET /api/admin/usuarios?busqueda=Gar`
- **THEN** el sistema retorna solo Usuarios cuyo nombre o apellidos contengan "Gar" (case-insensitive)

### Requirement: Sistema SHALL exponer endpoint de obtención de usuario por id

El sistema SHALL exponer `GET /api/admin/usuarios/{usuario_id}` que retorna los datos del Usuario (con PII descifrada). El endpoint requiere `usuarios:gestionar`.

#### Scenario: Obtener usuario existente

- **WHEN** un ADMIN hace `GET /api/admin/usuarios/{id}` para un Usuario existente en su tenant
- **THEN** el sistema retorna 200 con todos los campos del Usuario (PII descifrada)

#### Scenario: Usuario no encontrado retorna 404

- **WHEN** un ADMIN hace `GET /api/admin/usuarios/{id}` para un id inexistente
- **THEN** el sistema retorna 404 Not Found

#### Scenario: Usuario de otro tenant retorna 404

- **WHEN** un ADMIN de tenant A hace `GET /api/admin/usuarios/{id}` para un Usuario de tenant B
- **THEN** el sistema retorna 404 Not Found (no 403, para no revelar existencia)

### Requirement: Sistema SHALL exponer endpoint de actualización de usuario

El sistema SHALL exponer `PATCH /api/admin/usuarios/{usuario_id}` que actualiza campos editables del Usuario. Los campos PII se re-cifran al cambiar. El `id` y `tenant_id` son inmutables.

#### Scenario: Actualizar nombre y apellidos

- **WHEN** un ADMIN hace `PATCH /api/admin/usuarios/{id}` con `{"nombre": "Mariana"}`
- **THEN** el sistema actualiza el nombre a "Mariana"
- **AND** los demás campos permanecen sin cambios

#### Scenario: Actualizar email cambia el hash y re-cifra

- **WHEN** un ADMIN hace `PATCH /api/admin/usuarios/{id}` con `{"email": "nuevo@email.com"}`
- **THEN** el sistema re-cifra el email y recalcula `email_hash`
- **AND** retorna 200 con los datos actualizados

### Requirement: Sistema SHALL exponer endpoint de soft delete de usuario

El sistema SHALL exponer `DELETE /api/admin/usuarios/{usuario_id}` que realiza soft delete (setea `deleted_at`). No se debe realizar hard delete bajo ninguna circunstancia en el flujo normal.

#### Scenario: Soft delete de usuario

- **WHEN** un ADMIN hace `DELETE /api/admin/usuarios/{id}` para un Usuario existente
- **THEN** el sistema setea `deleted_at` al timestamp actual
- **AND** retorna 204 No Content
- **AND** el Usuario ya no aparece en listados normales

#### Scenario: Usuario soft-deleted no aparece en GET ni listados

- **WHEN** un Usuario fue soft-deleted
- **AND** un ADMIN hace `GET /api/admin/usuarios/{id}` o `GET /api/admin/usuarios`
- **THEN** el sistema retorna 404 (para GET by id) o no incluye el registro (para list)

### Requirement: Schemas de request/response SHALL usar `extra='forbid'`

Todos los schemas Pydantic de request y response para usuarios SHALL declarar `model_config = ConfigDict(extra="forbid")`, rechazando campos no declarados en el payload.

#### Scenario: Request con campo desconocido es rechazada

- **WHEN** se envía `POST /api/admin/usuarios` con `{"nombre": "X", "campo_inventado": 123}`
- **THEN** el sistema retorna 422 Unprocessable Entity

