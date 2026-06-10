## 1. Migración 006 — usuario, asignacion

- [x] 1.1 Crear `alembic/versions/006_usuarios_asignaciones.py` con `down_revision="005_estructura_academica"`
- [x] 1.2 Definir `upgrade()`: crear tabla `usuario` (id UUID PK→auth_user, tenant_id FK→tenant, email_hash, email_enc, dni_enc, cuil_enc, cbu_enc, alias_cbu_enc, nombre, apellidos, banco, regional, legajo, legajo_profesional, fecha_nacimiento, genero, observaciones, timestamps, deleted_at)
- [x] 1.3 Crear índice único `ix_usuario_tenant_email_hash` en `(tenant_id, email_hash)` y índice `ix_usuario_tenant_deleted`
- [x] 1.4 Definir `upgrade()`: crear tabla `asignacion` (id UUID PK, tenant_id FK→tenant, usuario_id FK→usuario, rol_id FK→rol, contexto_tipo enum Global|Carrera|Cohorte|Materia, contexto_id UUID nullable, responsable_id FK→usuario nullable, desde DATE, hasta DATE nullable, timestamps, deleted_at)
- [x] 1.5 Crear índices: `ix_asignacion_tenant_usuario`, `ix_asignacion_tenant_rol`, `ix_asignacion_tenant_contexto`, `ix_asignacion_tenant_deleted`
- [x] 1.6 Definir `downgrade()`: DROP TABLE IF EXISTS asignacion CASCADE, DROP TABLE IF EXISTS usuario CASCADE

## 2. Modelos ORM — Usuario y Asignacion

- [x] 2.1 Crear `app/models/usuario.py`: modelo `Usuario(Base, TenantScopedMixin)` con columnas PII cifradas (`email_enc`, `dni_enc`, `cuil_enc`, `cbu_enc`, `alias_cbu_enc` como `String` largo), `email_hash` (String(64)), campos planos (nombre, apellidos, banco, regional, legajo, legajo_profesional, fecha_nacimiento, genero, observaciones), e índices (`ix_usuario_tenant_email_hash` unique, `ix_usuario_tenant_deleted`)
- [x] 2.2 Crear `app/models/asignacion.py`: modelo `Asignacion(Base, TenantScopedMixin)` con enum `ContextoTipo` (Global, Carrera, Cohorte, Materia), columnas `contexto_tipo`, `contexto_id` UUID nullable, `usuario_id` FK→usuario, `rol_id` FK→rol, `responsable_id` FK→usuario nullable, `desde` DATE, `hasta` DATE nullable, e índices
- [x] 2.3 Implementar propiedad `estado_vigencia` en `Asignacion` (derivado: Vigente si desde ≤ today ≤ hasta, Vencida en otro caso; hasta=NULL implica sin límite superior)
- [x] 2.4 Implementar `__repr__` en ambos modelos SIN exponer PII
- [x] 2.5 Registrar modelos en `app/models/__init__.py`

## 3. Schemas Pydantic — extra='forbid'

- [x] 3.1 Crear `app/schemas/usuarios.py`: `UsuarioCreate` (nombre, apellidos, email, dni, cuil, cbu, alias_cbu, banco, regional, legajo?, legajo_profesional?, fecha_nacimiento?, genero?, observaciones?, id? opcional para vincular AuthUser existente)
- [x] 3.2 Agregar `UsuarioUpdate` (todos los campos editables como opcionales; id y tenant_id inmutables)
- [x] 3.3 Agregar `UsuarioResponse` (id, tenant_id, nombre, apellidos, email descifrado, dni descifrado, cuil descifrado, cbu descifrado, alias_cbu descifrado, banco, regional, legajo, legajo_profesional, fecha_nacimiento, genero, observaciones, created_at, updated_at)
- [x] 3.4 Crear `AsignacionCreate`, `AsignacionUpdate`, `AsignacionResponse` en `app/schemas/usuarios.py` (o `app/schemas/asignaciones.py`): incluir contexto_tipo, contexto_id, usuario_id, rol_id, responsable_id, desde, hasta
- [x] 3.5 Todos los schemas con `model_config = ConfigDict(extra="forbid")`

## 4. Repositorios y lógica de cifrado

- [x] 4.1 Crear `UsuarioRepository(TenantScopedRepository[Usuario])` con `find_by_email(tenant_id, email_lower)` usando `hash_email_for_search()`, mismo patrón que `AuthUserRepository`
- [x] 4.2 Implementar helper `_encrypt_fields(data, tenant_id)` que cifra email, dni, cuil, cbu, alias_cbu con sus `aad_suffix` respectivos
- [x] 4.3 Implementar helper `_decrypt_fields(usuario)` que descifra los campos PII para exposición en responses
- [x] 4.4 Sobrescribir `create()` en `UsuarioRepository` para: (a) validar unicidad de email vía `find_by_email`, (b) computar `email_hash` y `email_enc`, (c) cifrar campos PII, (d) delegar a `super().create()`
- [x] 4.5 Sobrescribir `update()` en `UsuarioRepository` para: si cambia email, validar unicidad y re-computar `email_hash`/`email_enc`; si cambian otros campos PII, re-cifrar

## 5. Services — UsuarioService y AsignacionService

- [x] 5.1 Crear `app/services/usuarios.py` con `UsuarioService(session, tenant_id)`: métodos `create(data)`, `get_by_id(id)`, `list(search?, limit, offset)`, `update(id, data)`, `delete(id)`
- [x] 5.2 `create()`: validar unicidad email, cifrar PII vía repository, validar `id` opcional (si se provee, verificar que AuthUser existe), manejar `IntegrityError` de email duplicado → 409
- [x] 5.3 `get_by_id()`: descifrar PII antes de retornar
- [x] 5.4 `list()`: soportar búsqueda textual en nombre/apellidos (ILIKE), paginación; descifrar PII en cada item
- [x] 5.5 `update()`: validar unicidad si cambia email, re-cifrar PII si cambia
- [x] 5.6 `delete()`: soft delete vía `repo.soft_delete(obj)`
- [x] 5.7 Crear `AsignacionService(session, tenant_id)`: métodos `create(data)`, `get_by_id(id)`, `list(filters)`, `update(id, data)`, `delete(id)`
- [x] 5.8 `create()`: validar `desde ≤ hasta`, validar existencia de usuario, rol y contexto (según `contexto_tipo`), validar responsable si se provee; todo debe ser del mismo tenant
- [x] 5.9 `list()`: soportar filtros por `usuario_id`, `rol_id`, `contexto_tipo`+`contexto_id`, `estado_vigencia`; incluir estado_vigencia derivado en cada item

## 6. Routers — `/api/admin/usuarios` y `/api/asignaciones`

- [x] 6.1 Crear `app/routers/usuarios.py`: `APIRouter(prefix="/api/admin", tags=["admin", "usuarios"])`
- [x] 6.2 `POST /api/admin/usuarios` con guard `Depends(require_permission("usuarios:gestionar"))`, response_model=UsuarioResponse, status 201
- [x] 6.3 `GET /api/admin/usuarios` con guard `usuarios:gestionar`, filtros `busqueda`, `limit`, `offset`
- [x] 6.4 `GET /api/admin/usuarios/{usuario_id}` con guard `usuarios:gestionar`
- [x] 6.5 `PATCH /api/admin/usuarios/{usuario_id}` con guard `usuarios:gestionar`
- [x] 6.6 `DELETE /api/admin/usuarios/{usuario_id}` con guard `usuarios:gestionar`, status 204
- [x] 6.7 Crear `GET /api/asignaciones`, `POST /api/asignaciones`, `GET /api/asignaciones/{id}`, `PATCH /api/asignaciones/{id}`, `DELETE /api/asignaciones/{id}` con guard `Depends(require_permission("equipos:asignar"))`
- [x] 6.8 Registrar ambos routers en `app/api/v1/main_router.py`

## 7. Tests unitarios — modelos y cifrado

- [x] 7.1 Crear `tests/unit/test_usuario_models.py`: test de creación de Usuario con campos PII cifrados (verificar que `email_enc != plaintext`, round-trip con `decrypt`), test de `email_hash` determinístico, test de unicidad (mismo email mismo tenant → error, distinto tenant → OK)
- [x] 7.2 Crear `tests/unit/test_asignacion_models.py`: test de `estado_vigencia` en todos los escenarios (sin hasta, con hasta futuro, con hasta pasado, desde futuro), test de contexto Global sin contexto_id, test de jerarquía responsable_id
- [x] 7.3 Test de que PII NUNCA se expone en `__repr__` ni logs: verificar que `repr(usuario)` no contiene email, dni, cuil, cbu, alias_cbu

## 8. Tests de integración — API

- [x] 8.1 Crear `tests/integration/test_usuario_api.py`: setup con tenant, AuthUser, y permisos - usar `mint_test_jwt` y `db_session`
- [x] 8.2 Test `POST /api/admin/usuarios`: creación exitosa, 403 sin permiso, 409 email duplicado, 422 campos inválidos
- [x] 8.3 Test `GET /api/admin/usuarios`: listado tenant-scoped, filtro por búsqueda, paginación
- [x] 8.4 Test `GET /api/admin/usuarios/{id}`: 200 con PII descifrada, 404 no encontrado, 404 otro tenant
- [x] 8.5 Test `PATCH /api/admin/usuarios/{id}`: actualización parcial, cambio de email re-cifra y actualiza hash
- [x] 8.6 Test `DELETE /api/admin/usuarios/{id}`: soft delete (204), GET posterior retorna 404
- [x] 8.7 Crear `tests/integration/test_asignacion_api.py`: setup con usuario, rol, carrera/cohorte/materia
- [x] 8.8 Test `POST /api/asignaciones`: creación con cada contexto_tipo, validación desde≤hasta, 403 sin `equipos:asignar`, 422 contexto inexistente
- [x] 8.9 Test `GET /api/asignaciones`: listado, filtro por usuario_id, filtro por contexto, filtro por estado_vigencia (vigentes vs vencidas)
- [x] 8.10 Test `PATCH /api/asignaciones`: actualizar hasta (vence asignación), actualizar contexto
- [x] 8.11 Test `DELETE /api/asignaciones/{id}`: soft delete 204
- [x] 8.12 Test aislamiento multi-tenant: usuario de tenant A no ve asignaciones de tenant B

## 9. Integración y registros

- [x] 9.1 Actualizar `tests/conftest.py` _ensure_schema_sync() para importar `app.models.usuario` y `app.models.asignacion`
- [x] 9.2 Verificar que `alembic upgrade head` aplica la migración 006 correctamente
- [x] 9.3 Ejecutar `pytest tests/ -x -v` y verificar que todos los tests pasan
