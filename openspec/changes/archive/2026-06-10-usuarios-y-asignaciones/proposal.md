## Why

Las entidades `Usuario` (E4) y `Asignacion` (E5) son las entidades raíz sobre las que se construye TODO el módulo de equipos docentes (C-08), padrón (C-09), calificaciones (C-10), encuentros (C-13), coloquios (C-14), avisos (C-15), tareas (C-16) y liquidaciones (C-18). Sin ellas, ningún módulo que vincule personas a roles en contextos académicos puede operar. La estructura académica (C-06) ya está disponible: carreras, cohortes y materias proveen los scopes de contexto para las asignaciones. Este change desbloquea el fork ancho de GATE 6.

## What Changes

- **Nuevo modelo `Usuario`** (`app/models/usuario.py`): entidad de dominio con PII cifrada (email, dni, cuil, cbu, alias_cbu) vía AES-256-GCM. Legajo es atributo de negocio opcional (no PK, no credencial). Comparte `id` (UUID) con `AuthUser` — la identidad criptográfica vive en auth, los datos personales viven en dominio.
- **Nuevo modelo `Asignacion`** (`app/models/asignacion.py`): vincula Usuario ↔ Rol con contexto acotado (Global, Carrera, Cohorte, Materia), jerarquía (`responsable_id`), vigencia `desde/hasta` y `estado_vigencia` derivado (Vigente/Vencida).
- **Unicidad `(tenant_id, email)`** a través de `email_hash` (HMAC, mismo patrón que `AuthUserRepository.find_by_email`).
- **ABM usuarios** en `/api/admin/usuarios` con guard `usuarios:gestionar` (ADMIN). CRUD con soft delete.
- **CRUD asignaciones** en `/api/asignaciones` con guard `equipos:asignar` (COORDINADOR, ADMIN). Las asignaciones vencidas se conservan para histórico.
- **Migración 006**: tablas `usuario` y `asignacion`. Down revision: `005_estructura_academica`.
- **Tests Strict TDD**: PII cifrada no expuesta en logs/respuestas, unicidad email por tenant, vigencia (vencida no autoriza), multi-rol, jerarquía responsable.

## Capabilities

### New Capabilities
- `usuario-pii-cifrada`: Almacenamiento y búsqueda de PII de usuarios del dominio con cifrado AES-256-GCM en reposo, email lookup por HMAC determinístico, y garantía de que los datos cifrados nunca se exponen en logs ni respuestas API.
- `usuario-crud`: ABM de usuarios del dominio (`/api/admin/usuarios`) con guard `usuarios:gestionar`, validación de unicidad de email por tenant, y soft delete. El endpoint de creación vincula opcionalmente un `AuthUser` existente por `id`.
- `asignacion-vigencia`: Asignación temporal de usuario a rol con fechas `desde/hasta`, estado de vigencia derivado (Vigente/Vencida), y garantía de que las asignaciones vencidas no otorgan permisos pero se conservan para auditoría.
- `asignacion-contexto`: Vinculación de asignaciones a un contexto académico (Global, Carrera, Cohorte, Materia) con FK polimórfica, jerarquía de responsable (`responsable_id`), y validación de integridad referencial contra las entidades de C-06.

### Modified Capabilities
<!-- None: this change adds new entities without modifying existing spec-level behavior. -->

## Impact

- **Nuevos archivos**: `app/models/usuario.py`, `app/models/asignacion.py`, `app/schemas/usuarios.py`, `app/services/usuarios.py`, `app/routers/usuarios.py`, `alembic/versions/006_usuarios_asignaciones.py`, `tests/unit/test_usuario_models.py`, `tests/unit/test_asignacion_models.py`, `tests/integration/test_usuario_api.py`, `tests/integration/test_asignacion_api.py`
- **Dependencias**: `app/core/security/crypto.py` (encrypt/decrypt), `app/core/security/hashing.py` (hash_email_for_search), `app/repositories/base.py` (get_tenant_repository), modelos de C-06 (carrera, cohorte, materia para FK de contexto), `app/rbac/models.py` (Rol para FK de asignación)
- **Permisos requeridos**: `usuarios:gestionar` y `equipos:asignar` (ya sembrados en C-04)
- **Migración 006**: depende de `005_estructura_academica` (C-06)
- **No modifica** specs existentes de auth (C-03) ni RBAC (C-04)
