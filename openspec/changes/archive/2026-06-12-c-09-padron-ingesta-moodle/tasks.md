# Tasks: C-09 — Padrón e Ingesta desde Moodle

## Implementación

### 1. Modelos y Migración

- [ ] **T-1.1** Crear migración `007: version_padron, entrada_padron`
  - Tabla `version_padron` con `id, tenant_id, materia_id, cohorte_id, cargado_por, cargado_at, activa`
  - Tabla `entrada_padron` con `id, version_id, tenant_id, usuario_id (nullable), nombre, apellidos, email, comision, regional`
  - Índices: `(materia_id, cohorte_id, activa)` en `version_padron`, `(version_id)` en `entrada_padron`
  - FK con `ondelete=CASCADE`

- [ ] **T-1.2** Crear modelos SQLAlchemy `VersionPadron` y `EntradaPadron`
  - Heredar de `TenantScopedMixin` y `TimestampMixin`
  - Soft delete en `VersionPadron`
  - Relación: `VersionPadron (1) → (N) EntradaPadron`

- [ ] **T-1.3** Crear schemas Pydantic `VersionPadronCreate`, `VersionPadronResponse`, `EntradaPadronCreate`, `EntradaPadronResponse`
  - `model_config = ConfigDict(extra='forbid')` en todos
  - `email` de `EntradaPadron` marcado como `[cifrado]` en comentarios (no en el schema)

### 2. Repository

- [ ] **T-2.1** Crear `PadronRepository` en `repositories/padron.py`
  - Método `create_version_and_entries()` atómico (crea VersionPadron + todas las EntradaPadron en una transacción)
  - Método `get_active_version(materia_id, cohorte_id)` — filtra por `activa=True`
  - Método `deactivate_all(materia_id, cohorte_id, version_id_except)` — desactiva todas las versiones existentes
  - Método `get_entries_by_version(version_id)` — lista entradas con join a `Usuario` (usuario_id puede ser null)
  - Método `vaciar_datos(materia_id, cohorte_id)` — soft delete de todas las versiones e entradas de esa materia/cohorte
  - Todos los métodos filtran por `tenant_id` del contexto

### 3. Servicio

- [ ] **T-3.1** Crear `PadronService` en `services/padron.py`
  - Método `import_padron(materia_id, cohorte_id, entries: list[EntradaPadronCreate], user_id)` — crea versión activa atómica, desactivando la anterior
  - Método `preview_padron(file_content: bytes, filename: str)` — parsea xlsx/csv y devuelve rows sin persistir
  - Método `vaciar_datos(materia_id, cohorte_id, user_id)` — llama al repository y emite audit log
  - Validación: rechazar archivos > 50MB, rechazar extensiones peligrosas (.exe, .php, .sh, .bat)

- [ ] **T-3.2** Crear parser de archivos en `services/padron_parser.py`
  - Función `parse_xlsx(content: bytes) -> list[dict]` — usa `openpyxl`
  - Función `parse_csv(content: bytes) -> list[dict]` — usa `csv.DictReader` con encoding detection (utf-8 → latin-1)
  - Función `detect_columns(headers: list[str]) -> dict` — mapea headers del archivo a campos del modelo (flexible: acepta variaciones como "Nombre", "nombre", "firstname", etc.)
  - Fallback encoding: `latin-1` si `utf-8` falla

### 4. Cliente Moodle WS

- [ ] **T-4.1** Crear `MoodleWSClient` en `integrations/moodle_ws.py`
  - Clase con `base_url`, `token`, `timeout` (default 30s), `max_retries` (default 3)
  - Método `get_users(course_id) -> list[dict]`
  - Método `get_activities(course_id) -> list[dict]`
  - Método `sync_enrollments(course_id, user_ids) -> bool`
  - Excepción `MoodleWSError` personalizada
  - Retry con exponential backoff usando `tenacity`
  - Logging de cada intento fallido

- [ ] **T-4.2** Integrar `MoodleWSClient` en router de padrones
  - `GET /api/padrones/moodle/sync/{materia_id}/{cohorte_id}` — sincroniza desde Moodle si está disponible
  - Si Moodle falla → `502 Bad Gateway` con mensaje de fallback manual
  - Permiso requerido: `padron:importar`

### 5. Router / Endpoints

- [ ] **T-5.1** Crear router `routers/padrones.py`
  - `POST /api/padrones/preview` — upload archivo, devuelve preview (sin persistir). Permiso: `padron:importar`
  - `POST /api/padrones` — persiste versión nueva con entries. Permiso: `padron:importar`
  - `GET /api/padrones/materia/{materia_id}/cohorte/{cohorte_id}` — lista versiones del padrón. Permiso: `padron:ver`
  - `GET /api/padrones/{version_id}/entradas` — lista entradas de una versión. Permiso: `padron:ver`
  - `PATCH /api/padrones/{version_id}/activar` — activa una versión (desactiva las demás). Permiso: `padron:importar`
  - `DELETE /api/padrones/materia/{materia_id}/cohorte/{cohorte_id}` — vaciar datos. Permiso: `padron:importar`
  - `GET /api/padrones/moodle/sync/{materia_id}/{cohorte_id}` — sync desde Moodle. Permiso: `padron:importar`

- [ ] **T-5.2** Registrar router en `app/main.py`

### 6. Permisos RBAC

- [ ] **T-6.1** Agregar permisos `padron:importar` y `padron:ver` al catálogo
  - Seed en migración o en el servicio de RBAC existente
  - `padron:importar` → PROFESOR, COORDINADOR, ADMIN
  - `padron:ver` → PROFESOR, COORDINADOR, ADMIN

### 7. Tests

- [ ] **T-7.1** Tests de integración: versionado (activar desactiva anterior)
- [ ] **T-7.2** Tests de integración: import xlsx/csv con preview y confirmación
- [ ] **T-7.3** Tests de integración: entrada sin `usuario_id` se persiste como null
- [ ] **T-7.4** Tests de integración: aislamiento tenant (tenant A no ve padron de B)
- [ ] **T-7.5** Tests de unidad: parser de xlsx y csv con encoding detection
- [ ] **T-7.6** Tests de integración: mock de Moodle WS con fallback 502
- [ ] **T-7.7** Tests de integración: vaciar datos de materia soft-deletes todo
- [ ] **T-7.8** Tests de seguridad: archivo > 50MB rechazado con 413

## Verificación

- [ ] **T-8.1** Correr todos los tests de padrones: `pytest tests/padrones/ -v`
- [ ] **T-8.2** Verificar cobertura ≥80% para el módulo `padron`
- [ ] **T-8.3** Correr `pytest` completo para asegurar que no se rompio nada