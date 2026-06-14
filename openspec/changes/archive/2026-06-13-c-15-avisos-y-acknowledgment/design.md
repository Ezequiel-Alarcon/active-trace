## Context

Current state: The platform has no notice/announcement system. Communications go through the Comunicacion module (outbound messaging with approval flow). Avisos fill a different niche — a persistent notice board visible to users on login/dashboard, with audience segmentation, time-bounded visibility, and optional acknowledgment tracking for compliance-sensitive notices.

This design builds on existing patterns: TenantScopedMixin for models, `require_permission` guard, `repository-base` for queries, and Alembic migrations with permission seeds.

## Goals / Non-Goals

**Goals:**
- Create Aviso model with audience segmentation (alcance, rol_destino, materia_id, cohorte_id), visibility window, severity, ordering, and acknowledgment requirement
- CRUD endpoints for COORDINADOR/ADMIN scoped to their tenant
- Read endpoint that returns only visible avisos for the authenticated user based on their roles and course/cohorte assignments
- Acknowledgment endpoint for users to confirm avisos that require it
- Migration 018_avisos.py with tables + permission seeds

**Non-Goals:**
- Real-time push notifications (out of scope; avisos are polled on load)
- Rich-text editor integration (body stored as text, frontend handles rendering)
- Acknowledgment reports or analytics dashboards
- Scheduling of avisos (visibility window is passive — no background job)

## Decisions

### D1: Alcance enums as database-level ENUM
Use a native PostgreSQL ENUM for `alcance` (Global, PorMateria, PorCohorte, PorRol) and `severidad` (Info, Advertencia, Crítico). Follows the existing `ContextoTipo`, `DiaSemana`, `EstadoEncuentro` pattern. Enums are stored as text-like values.

### D2: Acknowledgment as separate table (no denormalized counter)
`AcknowledgmentAviso` is a separate table with a FK to Aviso + Usuario. The counter (how many acknowledged) is computed via COUNT query rather than a denormalized `ack_count` column on Aviso. This is simpler and avoids sync issues. If performance becomes a concern later, a materialized view or counter cache can be added.

### D3: Visibility filtering in service layer, not database
The `list_visible` query builds a dynamic WHERE clause in the service layer:
- Base: `activo = true AND inicio_en <= now() AND fin_en >= now()`
- Global alcance: all visible avisos regardless of user's context
- PorRol: match autenticated user's role
- PorMateria: match user's materia assignments
- PorCohorte: match user's cohorte(s)
- rol_destino: if set, filtered additionally by the user's role

The query filters by `tenant_id` (handled by repository base), then applies audience rules.

### D4: Router naming follows existing pattern
- Base: `/api/avisos`
- CRUD: `POST /api/avisos`, `GET /api/avisos/{id}`, `PATCH /api/avisos/{id}`, `DELETE /api/avisos/{id}`
- Admin list: `GET /api/avisos` (all avisos for management, paginated)
- User visible: `GET /api/avisos/mis-avisos` (filtered by visibility rules)
- Acknowledgment: `POST /api/avisos/{id}/acknowledge`
- Counter: `GET /api/avisos/{id}/acknowledgment`

### D5: Permission scheme
- `avisos:publicar` → COORDINADOR, ADMIN (create, update, delete, list all)
- `avisos:confirmar` → all authenticated users (read visible + acknowledge)

Uses the existing `require_permission` guard pattern from `app/core/permissions.py`.

## Risks / Trade-offs

- **Risk**: Visibility query complexity grows as more alcance types combine with rol_destino. → Mitigation: each alcance is a clear branch with single responsibility; add integration tests for each combination.
- **Risk**: Acknowledgment table could grow large in high-tenant deployments. → Mitigation: indexed by (aviso_id, usuario_id) unique; soft delete not needed (immutable records).
- **Trade-off**: Choosing service-layer filtering over SQL-level means more data may be fetched from DB than returned. Acceptable for notice board volumes (tens/hundreds, not millions).
