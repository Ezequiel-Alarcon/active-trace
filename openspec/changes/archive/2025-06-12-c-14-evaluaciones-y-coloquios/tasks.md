## 1. Models & Migration

- [ ] 1.1 Create `backend/app/models/evaluacion.py` with `Evaluacion`, `ReservaEvaluacion`, `ResultadoEvaluacion` models using `TenantScopedMixin` and soft delete
- [ ] 1.2 Create Alembic migration `016_evaluaciones.py` for the three new tables with JSONB dias column
- [ ] 1.3 Import models in `backend/app/models/__init__.py`

## 2. Schemas

- [ ] 2.1 Create `backend/app/schemas/evaluaciones.py` with all request/response Pydantic schemas using `extra='forbid'`
  - `EvaluacionCreate`, `EvaluacionResponse`, `EvaluacionListResponse` (with metrics)
  - `ReservaCreate`, `ReservaResponse`
  - `ResultadoCreate`, `ResultadoResponse`
  - `ColoquioMetricsResponse`

## 3. Repository

- [ ] 3.1 Create `backend/app/repositories/evaluaciones.py` with `ColoquioRepository` extending `TenantScopedRepository`
  - Methods: `get_evaluacion`, `list_evaluaciones`, `create_evaluacion`, `update_evaluacion`
  - Methods: `get_reserva`, `list_reservas_by_evaluacion`, `create_reserva`, `cancel_reserva`
  - Methods: `list_resultados`, `upsert_resultado`
  - Methods: `count_reservas_activas`, `get_convocados_count`, `get_reservas_count_by_fecha`

## 4. Service

- [ ] 4.1 Create `backend/app/services/evaluaciones.py` with `ColoquioService`
  - `create_evaluacion(data, dias)` — generates dias JSONB array, validates materia/cohorte exist
  - `list_evaluaciones()` — returns list with computed metrics
  - `get_evaluacion(id)` — single evaluation with full detail
  - `close_evaluacion(id)` — sets estado to Cerrada
  - `importar_alumnos(evaluacion_id, alumno_ids)` — creates ResultadoEvaluacion entries
  - `get_metricas()` — aggregated metrics across tenant
  - `create_reserva(evaluacion_id, alumno_id, fecha)` — validates cupos, creates ReservaEvaluacion
  - `cancel_reserva(reserva_id, alumno_id)` — validates ownership, sets Cancelada
  - `list_mis_reservas(alumno_id)` — student's own reservations
  - `list_reservas_by_evaluacion(evaluacion_id)` — all reservations for an evaluation
  - `upsert_resultado(evaluacion_id, alumno_id, nota_final)` — create or update ResultadoEvaluacion
  - `list_resultados(evaluacion_id)` — consolidated results

## 5. Router

- [ ] 5.1 Create `backend/app/routers/coloquios.py` with all endpoints
  - `POST /api/coloquios` — create convocation (coloquios:gestionar)
  - `GET /api/coloquios` — list with metrics (coloquios:ver)
  - `GET /api/coloquios/metricas` — aggregated metrics (coloquios:ver)
  - `GET /api/coloquios/{evaluacion_id}` — single evaluation (coloquios:ver)
  - `POST /api/coloquios/{evaluacion_id}/importar` — import students (coloquios:gestionar)
  - `PATCH /api/coloquios/{evaluacion_id}/cerrar` — close convocation (coloquios:gestionar)
  - `POST /api/coloquios/{evaluacion_id}/reservas` — student reserves slot (coloquios:reservar)
  - `GET /api/coloquios/mis-reservas` — student's own reservations (any authenticated)
  - `GET /api/coloquios/{evaluacion_id}/reservas` — list all reservas (coloquios:ver)
  - `PATCH /api/coloquios/reservas/{reserva_id}/cancelar` — cancel reservation (coloquios:reservar)
  - `POST /api/coloquios/{evaluacion_id}/resultados` — record result (coloquios:gestionar)
  - `GET /api/coloquios/{evaluacion_id}/resultados` — list results (coloquios:ver)

## 6. Permissions

- [ ] 6.1 Add `coloquios:gestionar`, `coloquios:ver`, `coloquios:reservar` permissions to RBAC catalogue
- [ ] 6.2 Register router in `backend/app/main.py`

## 7. Tests

- [ ] 7.1 Create `backend/tests/test_coloquios.py` with real DB tests:
  - Test slot creation with cupos, reservation decrements cupos, no-cupo rejects, metrics aggregation, consolidated results
- [ ] 7.2 Run tests and fix any failures