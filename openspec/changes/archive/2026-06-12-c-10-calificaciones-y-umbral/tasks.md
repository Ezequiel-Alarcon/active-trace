## 1. Database Migrations

- [x] 1.1 Create Alembic migration: add `calificacion` table (id, tenant_id, materia_id, usuario_id, asignacion_id, version_padron_id, nota JSONB, origen, import_batch_id, created_at, created_by, deleted_at) with unique constraint on (materia_id, usuario_id, asignacion_id, deleted_at)
- [x] 1.2 Create Alembic migration: add `umbral_materia` table (id, tenant_id, materia_id, asignacion_id, umbral_pct, conjunto_aprobado JSONB, created_at, created_by, deleted_at) with unique constraint on (materia_id, asignacion_id, deleted_at)
- [x] 1.3 Create Alembic migration: seed default `UmbralMateria` (umbral_pct=60, conjunto_aprobado=["A","B+","C","7","8","9","10"]) for all existing materias with asignacion_id=null

## 2. Domain Models

- [x] 2.1 Create `src/domain/calificaciones/models/calificacion.py`: SQLAlchemy model Calificacion with all fields, relationships (materia, usuario, asignacion, version_padron, umbral_materia via asignacion), unique constraint, soft delete
- [x] 2.2 Create `src/domain/calificaciones/models/umbral_materia.py`: SQLAlchemy model UmbralMateria with all fields, relationships (materia, asignacion), unique constraint, soft delete
- [x] 2.3 Create `src/domain/calificaciones/models/__init__.py`: export both models

## 3. Pydantic Schemas

- [x] 3.1 Create `src/domain/calificaciones/schemas/calificacion.py`: CalificacionBase, CalificacionCreate, CalificacionRead (with aprobado derived), CalificacionPreviewRow (with valid, warnings fields), CalificacionPreviewResponse (with preview_token, rows)
- [x] 3.2 Create `src/domain/calificaciones/schemas/umbral_materia.py`: UmbralMateriaBase, UmbralMateriaCreate, UmbralMateriaRead, UmbralMateriaUpdate
- [x] 3.3 Create `src/domain/calificaciones/schemas/__init__.py`: export all schemas
- [x] 3.4 Add `origen` enum: Importado, Manual in schemas

## 4. Repositories

- [x] 4.1 Create `src/domain/calificaciones/repositories/calificacion.py`: CalificacionRepository with methods: create_many (batch insert), get_filtered (by materia, usuario, asignacion, pagination), get_by_materia_usuario_asignacion (for duplicate detection)
- [x] 4.2 Create `src/domain/calificaciones/repositories/umbral_materia.py`: UmbralMateriaRepository with methods: get_by_materia_asignacion (with fallback), create, update, get_default_for_materia
- [x] 4.3 Create `src/domain/calificaciones/repositories/__init__.py`: export both repositories

## 5. Services

- [x] 5.1 Create `src/domain/calificaciones/services/aprobado.py`: `derivar_aprobado(nota, umbral_pct, conjunto_aprobado) -> bool` implementing the 3-case logic (null → False, numeric >= umbral_pct, string/list in conjunto)
- [x] 5.2 Create `src/domain/calificaciones/services/import_service.py`: ImportService with methods: parse_preview(file, type) → PreviewResult, confirm_import(preview_token) → ConfirmResult. Manages preview_token in-memory store (15-min TTL, single-use)
- [x] 5.3 Create `src/domain/calificaciones/services/calificacion_service.py`: CalificacionService with methods: list_calificaciones (with aprobado derived), create_calificacion (manual), get_calificacion_by_id
- [x] 5.4 Create `src/domain/calificaciones/services/umbral_service.py`: UmbralService with methods: get_umbral_for_asignacion (with fallback), create_umbral, update_umbral
- [x] 5.5 Create `src/domain/calificaciones/services/__init__.py`: export all services

## 6. API Endpoints

- [x] 6.1 Create `src/api/v1/calificaciones.py`: router with GET / (listar), POST / (crear manual), POST /import/preview, POST /import/confirm. All endpoints use `require_permission("calificaciones:importar")` or `calificaciones:ver` as appropriate
- [x] 6.2 Create `src/api/v1/umbral_materia.py`: router with GET / (listar), POST / (crear), PUT /{id} (actualizar). POST/PUT require `calificaciones:importar`, GET requires `calificaciones:ver`
- [x] 6.3 Register routers in `src/api/v1/__init__.py` and include in main FastAPI app

## 7. Audit

- [x] 7.1 Ensure audit log entry is written on confirm: operacion=CALIFICACIONES_IMPORTAR, detalle includes import_batch_id, total_filas, persistidas, omitidas, usuario_id, tenant_id from JWT

## 8. Tests

- [x] 8.1 Write unit tests for `derivar_aprobado`: null nota → False, numeric >= umbral → True, numeric < umbral → False, string in conjunto → True, string not in conjunto → False, list with any match → True, list with no match → False
- [x] 8.2 Write integration tests for import flow: upload valid CSV → preview returns token + rows → confirm persists records + audit log entry
- [x] 8.3 Write integration tests for duplicate detection: importing same usuario+asignacion twice → second row marked invalid in preview
- [x] 8.4 Write tests for umbral fallback: assignment-specific umbral takes precedence over course default
- [x] 8.5 Write tests for tenant isolation: tenant A's calificaciones not visible to tenant B