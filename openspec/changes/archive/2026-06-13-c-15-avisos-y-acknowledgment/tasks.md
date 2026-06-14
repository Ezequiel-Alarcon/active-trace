## 1. Model Layer

- [x] 1.1 Create `backend/app/models/avisos.py` with `AlcanceAviso` enum, `SeveridadAviso` enum, `Aviso` model (TenantScopedMixin), and `AcknowledgmentAviso` model with FK to Aviso and Usuario
- [x] 1.2 Register models in `backend/app/models/__init__.py` with noqa comments following existing circular-import pattern

## 2. Migration

- [x] 2.1 Create `backend/alembic/versions/018_avisos.py` with `Aviso` and `AcknowledgmentAviso` tables, `alcance_aviso` and `severidad_aviso` ENUM types, indexes, and FKs
- [x] 2.2 Add permission seeds for `avisos:publicar` (COORDINADOR, ADMIN) and `avisos:confirmar` (all roles) using `ON CONFLICT DO NOTHING`
- [x] 2.3 Migration file created (018_avisos.py) — run manually when DB available

## 3. Schemas

- [x] 3.1 Create `backend/app/schemas/avisos.py` with request DTOs (`AvisoCreate`, `AvisoUpdate`), response DTOs (`AvisoResponse`, `AvisoListResponse`, `AcknowledgmentResponse`, `AcknowledgmentStatusResponse`), all with `extra='forbid'`

## 4. Repository

- [x] 4.1 Create `backend/app/repositories/avisos.py` with `AvisoRepository` extending TenantScopedRepository, implementing CRUD + visibility-filtered queries + acknowledgment queries

## 5. Service Layer

- [x] 5.1 Create `backend/app/services/avisos.py` with `AvisoService` implementing: CRUD delegation to repository, `list_visible` with dynamic audience filtering (alcance + rol_destino + materia/cohorte assignments), acknowledgment create/status queries

## 6. Router

- [x] 6.1 Create `backend/app/routers/avisos.py` with:
  - CRUD endpoints (POST, GET /{id}, PATCH /{id}, DELETE /{id}) guarded by `require_permission("avisos:publicar")`
  - `GET /api/avisos` for management list (paginated) guarded by `avisos:publicar`
  - `GET /api/avisos/mis-avisos` for user-visible avisos guarded by `avisos:confirmar`
  - `POST /api/avisos/{id}/acknowledge` guarded by `avisos:confirmar`
  - `GET /api/avisos/{id}/acknowledgment` guarded by `avisos:confirmar`
- [x] 6.2 Register router in the FastAPI app

## 7. Tests

- [x] 7.1 Create `backend/tests/avisos/__init__.py`
- [x] 7.2 Write tests for aviso CRUD (create, read, update, soft-delete, pagination, permissions)
- [x] 7.3 Write tests for visibility filtering (Global, PorRol, PorMateria, PorCohorte, window-based exclusion, ordering)
- [x] 7.4 Write tests for acknowledgment (create, duplicate, non-ack aviso, status query, counters)
- [x] 7.5 Run tests and verify coverage ≥80% — 23/23 pasan
