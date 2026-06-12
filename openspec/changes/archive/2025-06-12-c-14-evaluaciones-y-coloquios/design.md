## Context

The current system lacks any evaluation colloquium management. We need to implement C-14 to support oral evaluations (coloquios) with:
- Convocation creation with configurable days and per-day capacity
- Student self-service reservation system
- Result recording
- Metrics dashboard for coordinators

Based on KB models E14 (Evaluacion, ReservaEvaluacion, ResultadoEvaluacion) and FL-07.

## Goals / Non-Goals

**Goals:**
- Multi-tenant isolated evaluation management
- Day-based slot reservations with capacity limits
- Student can reserve/cancel their own reservation
- Coordinators see metrics (convocados/reservas/libres)
- Soft delete on all entities

**Non-Goals:**
- Scheduling conflicts detection (two students same slot)
- Email notifications (handled by separate C-13)
- Integration with LMS gradebook (future)

## Decisions

1. **Day + capacity model**: Each `Evaluacion` has `dias_disponibles` (integer). The system auto-generates N days of slots starting from `fecha_inicio`. Each day has `cupos` (passed at creation). Students book a day, not a specific hour.

2. **Convocation as single entity**: A convocation = one `Evaluacion` record. Days/cupos are stored in the `dias` JSONB column on `Evaluacion`. This avoids a separate "DaySlot" table for simpler queries.

3. **ReservaEvaluacion tracks student's chosen day**: The `fecha_hora` field stores the date (not datetime) the student reserved. State machine: Activa → Cancelada.

4. **Metrics derived at query time**: No denormalized counters. Count active reservas per evaluacion to compute free capacity.

5. **Permission model**:
   - `coloquios:gestionar` — COORDINADOR, ADMIN (create, import, close)
   - `coloquios:ver` — COORDINADOR, ADMIN (list, metrics)
   - `coloquios:reservar` — ALUMNO (own reservation only)

## Risks / Trade-offs

- [Risk] JSONB dias structure is flexible but harder to query per-day from SQL. → Mitigation: JSONB array with index on evaluacion_id. For metrics we query ReservaEvaluacion count grouped by evaluacion_id.
- [Risk] Capacity race condition (two students book same slot simultaneously). → Mitigation: Use `SELECT FOR UPDATE` on evaluacion row when creating reserva, or optimistic locking with version column.
- [Risk] Large number of students per convocation (100+). → Mitigation: Pagination on list endpoints, cursor-based for reserva queries.