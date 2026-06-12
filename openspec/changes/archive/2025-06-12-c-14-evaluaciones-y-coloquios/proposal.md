## Why

The system needs a complete evaluation and colloquium management module (C-14) to handle formal oral evaluations. Currently there's no way to create evaluation calls, manage available slots with capacity limits, allow students to reserve time slots, or track results. This blocksÉpica 7 (F7.1-F7.5) and FL-07 from being implemented.

## What Changes

- New models: `Evaluacion`, `ReservaEvaluacion`, `ResultadoEvaluacion` with multi-tenant isolation
- Colloquium convocation management (create, list, metrics) for COORDINADOR/ADMIN
- Student self-service slot reservation (ALUMNO sees available days with capacity, reserves a slot)
- Metrics panel showing: total called, active reservations, free capacity
- Import students to a convocation
- Result recording and consolidated academic record view
- API endpoints under `/api/coloquios/*` with proper RBAC
- Alembic migration for new tables
- Unit tests covering: slot creation with capacity, reservation decrements capacity, no-capacity rejection, metrics aggregation, consolidated results

## Capabilities

### New Capabilities
- `coloquio-evaluacion`: Create/list/manage evaluation convocations (COORDINADOR/ADMIN), import students, view metrics panel
- `reserva-turno`: Student reserves a slot from available days with capacity; Cancel reservation; view personal reservations
- `resultado-evaluacion`: Record and query final grades/results for evaluated students

### Modified Capabilities
- None

## Impact

- New tables: `evaluacion`, `reserva_evaluacion`, `resultado_evaluacion` (with `tenant_id` and soft-delete)
- New API router: `api/coloquios/*`
- New service: `ColoquioService`
- New repository: `ColoquioRepository`
- RBAC permissions: `coloquios:gestionar`, `coloquios:ver`, `coloquios:reservar`
- Audit events: `EVALUACION_CREAR`, `RESERVA_CREAR`, `RESERVA_CANCELAR`, `RESULTADO_REGISTRAR`