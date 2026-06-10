## Context

El proyecto ya cuenta con `AuthUser` (autenticación: password_hash, TOTP) y el catálogo RBAC (`Rol`, `Permiso`, `RolPermiso`) sembrado. La estructura académica (`Carrera`, `Cohorte`, `Materia`) de C-06 provee los scopes de contexto. El helper de cifrado AES-256-GCM (`app/core/security/crypto.py`) y el HMAC de búsqueda (`app/core/security/hashing.py`) están operativos.

Este change introduce las dos entidades raíz que vinculan personas reales a roles en contextos académicos: `Usuario` (datos personales con PII cifrada) y `Asignacion` (vínculo Usuario ↔ Rol ↔ contexto con vigencia temporal). Todo el fork de GATE 6 depende de esto.

## Goals / Non-Goals

**Goals:**
- Modelo `Usuario` con PII cifrada en reposo (email, dni, cuil, cbu, alias_cbu) y búsqueda de email por HMAC determinístico
- Modelo `Asignacion` con vigencia `desde/hasta`, estado derivado Vigente/Vencida, y contexto polimórfico (global, carrera, cohorte, materia)
- ABM de usuarios (`/api/admin/usuarios`) protegido con `usuarios:gestionar`
- CRUD de asignaciones (`/api/asignaciones`) protegido con `equipos:asignar`
- Soft delete en ambas entidades
- Unicidad `(tenant_id, email)` vía `email_hash`
- Migración 006 atómica que crea ambas tablas

**Non-Goals:**
- No modifica el flujo de auth (C-03) — `Usuario` es una entidad de dominio separada de `AuthUser`
- No implementa asignación masiva ni clonado de equipos (eso es C-08)
- No resuelve permisos efectivos basados en asignaciones (la resolución actual de C-04 usa `rol_permiso`, la integración con `Asignacion` es parte de C-08)
- No expone endpoints de búsqueda pública de usuarios (solo ADMIN gestiona)

## Decisions

### D1: Usuario comparte `id` con AuthUser

**Decisión**: `Usuario.id` es el mismo UUID que `AuthUser.id` cuando existe un registro auth asociado. La FK es `usuario.id → auth_user.id` con ON DELETE RESTRICT. Un `Usuario` puede existir sin `AuthUser` (alumno sin cuenta todavía), pero cuando existe es el mismo UUID.

**Alternativa considerada**: `usuario.auth_user_id` como FK nullable. Se descartó porque el vínculo 1:1 es la regla (C-09/C-07), y tener dos UUIDs distintos para la misma persona agrega complejidad innecesaria en joins posteriores. La identidad es una sola.

**Rationale**: KB 04 §E4 define `Usuario.id` como "same as auth_user.id". El patrón es limpio: auth maneja credenciales, domain maneja datos personales, mismo UUID.

### D2: Email lookup por HMAC (mismo patrón que AuthUser)

**Decisión**: `usuario.email_hash` almacena `HMAC-SHA256(ENCRYPTION_KEY, f"{tenant_id}:{email_lower}")`. El lookup usa `hash_email_for_search()` (misma función que `AuthUserRepository.find_by_email`). El ciphertext en `usuario.email_enc` es solo para confidencialidad al desencriptar.

**Alternativa considerada**: índice sobre ciphertext. Descartado porque AES-GCM con nonce aleatorio produce ciphertexts distintos para el mismo plaintext — no sirve para equality lookup.

**Rationale**: Mismo patrón que C-03 probó en `auth_user`. Reusa `hash_email_for_search()` sin duplicar.

### D3: Cifrado por campo con `aad_suffix` único

**Decisión**: Cada campo PII usa un `aad_suffix` distinto al cifrar/descifrar:
- `email` → `aad_suffix="usuario.email"`
- `dni` → `aad_suffix="usuario.dni"`
- `cuil` → `aad_suffix="usuario.cuil"`
- `cbu` → `aad_suffix="usuario.cbu"`
- `alias_cbu` → `aad_suffix="usuario.alias_cbu"`

Esto asegura que un ciphertext de email no pueda ser descifrado como dni aunque el atacante tenga la clave.

**Rationale**: Contrato de `core/security/crypto.py` — el AAD se valida en `decrypt()` y un mismatch de `aad_suffix` produce error de autenticación. Sin costo adicional.

### D4: `estado_vigencia` derivado, no persistido

**Decisión**: `Asignacion.estado_vigencia` se computa como propiedad Python:
```
Vigente si desde <= today() AND (hasta IS NULL OR hasta >= today())
Vencida en caso contrario
```
No se persiste en DB. La columna existe en el modelo como `@property` o `column_property` para que SQLAlchemy pueda incluirla en queries si fuera necesario, pero el valor se calcula al vuelo.

**Alternativa considerada**: Columna materializada con job nocturno. Descartada por complejidad innecesaria — el cálculo es O(1) y siempre determinístico.

**Rationale**: KB 04 §E5 dice "derivado". El valor cambia automáticamente al cruzar `hasta`, sin necesidad de batch jobs.

### D5: Contexto polimórfico con enum + FK única

**Decisión**: `contexto_tipo` es un enum SQL (`Global`, `Carrera`, `Cohorte`, `Materia`) y `contexto_id` es un UUID nullable. Cuando `contexto_tipo = Global`, `contexto_id` es NULL. Para los demás valores, `contexto_id` referencia la entidad correspondiente (`carrera.id`, `cohorte.id`, `materia.id`).

**Alternativa considerada**: Tablas separadas por tipo de contexto (asignacion_carrera, asignacion_cohorte, etc.). Descartado porque duplica esquema y complica queries de "todas las asignaciones de un usuario".

**Rationale**: KB 04 §E5 define exactamente este esquema. La integridad referencial por tipo se valida en capa de servicio (no hay FK polimórfica nativa en PostgreSQL sin CHECK constraints complejas).

### D6: Índice de unicidad compuesto para email

**Decisión**: `CREATE UNIQUE INDEX ix_usuario_tenant_email_hash ON usuario (tenant_id, email_hash)`. El hash es determinístico y fijo para un `(tenant_id, email)`, por lo que el índice único funciona correctamente.

**Rationale**: Mismo patrón que `ix_auth_user_tenant_email_hash`. La unicidad se garantiza a nivel DB, no solo en aplicación.

### D7: Soft delete conserva asignaciones vencidas

**Decisión**: Tanto `Usuario` como `Asignacion` usan `TenantScopedMixin` → `deleted_at`. El soft delete es el único mecanismo de borrado. Las asignaciones vencidas (estado Vencida) NO se borran — se conservan para trazabilidad histórica de quién tuvo qué rol en qué período.

**Rationale**: Regla dura del proyecto: soft delete siempre. KB 03 §5: asignaciones vencidas se conservan para auditoría.

## Risks / Trade-offs

- **[Riesgo] FK polimórfica sin constraint DB**: `contexto_id` puede apuntar a una entidad inexistente si alguien hace hard-delete (violando soft-delete). → **Mitigación**: validación en capa de servicio antes de crear/actualizar asignación. Hard delete solo por `unsafe_physical_delete` (admin scripts).
- **[Riesgo] Email duplicado entre tenant**: race condition entre check y create. → **Mitigación**: el índice único en DB es la última línea de defensa; la app captura `IntegrityError` y lo mapea a 409.
- **[Riesgo] Rotación de `ENCRYPTION_KEY`**: ciphertexts cifrados con clave antigua fallan al descifrar con clave nueva. → **Mitigación**: el helper `crypto.py` ya soporta `key_id` en el envelope. La rotación se maneja a nivel infra (fuera de scope de este change).
- **[Riesgo] Asignación sin `hasta` es indefinida**: puede acumularse sin cleanup. → **Mitigación**: C-08 (equipos docentes) implementa operaciones de vigencia masiva y clonado entre cohortes para manejar esto.

## Migration Plan

1. **Crear migración 006**: `alembic revision -m "006_usuarios_asignaciones"` con `down_revision="005_estructura_academica"`.
2. **Upgrade**: crea `usuario` (con índice unique `(tenant_id, email_hash)`) y `asignacion` (con FK a `usuario`, `rol`, y contexto). Orden: primero `usuario` (porque `asignacion.usuario_id` lo referencia).
3. **Rollback**: `DROP TABLE IF EXISTS asignacion CASCADE; DROP TABLE IF EXISTS usuario CASCADE`.
4. **No hay migración de datos** — estas son tablas nuevas, sin datos previos que migrar.
5. **Deploy**: migration se aplica con `alembic upgrade head`. Si falla, rollback inmediato con `alembic downgrade -1`.

## Open Questions

<!-- Todas las decisiones de diseño están cerradas. Los puntos abiertos (PA-01, PA-07, PA-22, PA-23, PA-25) aplican a otros cambios (C-06, C-18), no a este. -->
