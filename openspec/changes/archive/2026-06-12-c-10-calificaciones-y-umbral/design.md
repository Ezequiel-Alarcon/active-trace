# C-10: Calificaciones y Umbral — Design

## Context

C-09 (padron-ingesta-moodle) populates `VersionPadron`, `Materia`, and `Usuario` from Moodle data. C-10 builds on that foundation to store grades (`Calificacion`) and define approval thresholds (`UmbralMateria`) so the system can determine which students passed and feed that data downstream (e.g., Finanzas for honorarios).

The domain requires:
- A `Calificacion` model linked to `materia_id`, `usuario_id`, and optionally `version_padron_id` (to track which LMS import produced it)
- An `UmbralMateria` model that stores per-assignment thresholds (default 60%)
- A 2-step import flow: preview (parse + validate without persisting) → confirm (persist + audit)
- The `aprobado` flag is derived, not stored: numérica > umbral, textual ∈ conjunto_aprobado, null → False

## Goals / Non-Goals

**Goals:**
- Store grades imported from LMS (grades + completion report) with full tenant isolation
- Support manual grade entry alongside imports
- Provide configurable approval thresholds per assignment (materia × asignacion)
- Derive `aprobado` consistently from nota + umbral
- Full audit trail: who imported what and when

**Non-Goals:**
- Grade editing UI — only import + threshold config via API
- Grade calculation or weighted averages
- Integration with Moodle gradebook write-back
- Grade history / version tracking (soft-delete is sufficient)

## Decisions

### Decision 1: `nota` as nullable JSONB (numeric | text | set)

**Choice**: `calificacion.nota` is `JSONB` (nullable), stored as:
- Number: `7.5`
- Text: `"Aprobado"`
- Set: `["A", "B+", "C"]`
- `null`: TP submitted but not graded (from completion report)

**Rationale**: LMS grades are heterogeneous (numeric scales, letter grades, qualitative feedback). Using a single JSONB column avoids type-specific columns and handles all cases. The alternative (separate `nota_numerica`, `nota_texto`, `nota_conjunto` columns) creates NULL complexity and UNION queries.

**Alternatives considered**:
- Separate nullable columns per type → many NULLs, harder to query "all passing grades"
- EAV (entity-attribute-value) → over-normalized, bad query performance

### Decision 2: `aprobado` derived at query time, not stored

**Choice**: `aprobado` is computed by the service layer when reading `Calificacion` (never stored).

**Rationale**: `aprobado` depends on `UmbralMateria`, which is configurable and can change after grades are imported. Storing it would require re-derivation on every threshold change or accept stale data. Computing on read guarantees correctness.

**Alternatives considered**:
- Store `aprobado` on import, re-derive on threshold change → extra write + eventual consistency
- Trigger/procedure to maintain it → hidden coupling, hard to audit

### Decision 3: 2-step import (preview → confirm) via session token

**Choice**: `POST /api/calificaciones/import/preview` returns a `preview_token` (UUID) and a list of parsed rows (without persisting). `POST /api/calificaciones/import/confirm` accepts that token and persists.

**Rationale**: Preview needs to show the user exactly what will be imported — including rows that would be rejected (duplicates, missing users, invalid grades) — without modifying state. The token prevents race conditions between preview and confirm. The alternative (single POST with a `dry_run` flag) mixes read and write concerns and is not idempotent-safe.

**Alternatives considered**:
- Single POST with `dry_run=true` → still mutates preview state on the server
- Client sends all rows twice → wastes bandwidth, error-prone

### Decision 4: `UmbralMateria` scoped by `asignacion_id`, not `materia_id`

**Choice**: `UmbralMateria.asignacion_id` references `asignacion` (Moodle assignment/activity), with fallback to `materia_id` defaults.

**Rationale**: Different activities within the same course often have different passing requirements (e.g., TP threshold 60%, Parcial threshold 70%). If no assignment-specific threshold exists, the service falls back to the course-level default.

**Alternatives considered**:
- Per-materia only → too coarse
- Per-materia + per-activity override → same as this decision

### Decision 5: `origen` enum: `Importado` | `Manual`

**Choice**: `calificacion.origen` tracks how the grade entered the system.

**Rationale**: Imports can be audited and potentially reversed. Manual entries are attributed to the current user. The audit log records the full import batch vs. individual manual entries.

## Data Models

### Calificacion

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `tenant_id` | UUID | FK → tenant, always filtered |
| `materia_id` | UUID | FK → materia (from C-09) |
| `usuario_id` | UUID | FK → usuario (student) |
| `asignacion_id` | UUID | FK → asignacion (Moodle activity), nullable |
| `version_padron_id` | UUID | FK → version_padron (which import), nullable |
| `nota` | JSONB | null \| number \| string \| string[] |
| `origen` | Enum | `Importado`, `Manual` |
| `import_batch_id` | UUID | Groups rows from same import, nullable |
| `created_at` | DateTime | UTC |
| `created_by` | UUID | User who created (from JWT) |
| `deleted_at` | DateTime | Soft delete |

**Constraints**: Unique `(materia_id, usuario_id, asignacion_id, deleted_at)` — one grade per student per activity.

### UmbralMateria

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `tenant_id` | UUID | FK → tenant |
| `materia_id` | UUID | FK → materia |
| `asignacion_id` | UUID | FK → asignacion, nullable (null = course-level default) |
| `umbral_pct` | Integer | 0–100, default 60 |
| `conjunto_aprobado` | JSONB | Array of strings, e.g. `["A","B+","C","7"]` |
| `created_at` | DateTime | UTC |
| `created_by` | UUID | From JWT |
| `deleted_at` | DateTime | Soft delete |

**Constraints**: Unique `(materia_id, asignacion_id, deleted_at)` per tenant.

## Lógica de Derivación `aprobado`

```python
def derivar_aprobado(nota: Any, umbral: UmbralMateria) -> bool:
    if nota is None:
        return False  # TP entregada sin calificar → no aprobado
    if isinstance(nota, (int, float)):
        return nota >= umbral.umbral_pct
    if isinstance(nota, str):
        return nota in (umbral.conjunto_aprobado or [])
    if isinstance(nota, list):
        return any(item in (umbral.conjunto_aprobado or []) for item in nota)
    return False
```

## API Endpoints

| Method | Path | Permiso | Descripción |
|--------|------|---------|-------------|
| `GET` | `/api/calificaciones` | `calificaciones:ver` | Listar calificaciones (filter by materia, usuario, asignacion) |
| `POST` | `/api/calificaciones` | `calificaciones:importar` | Crear/importar una calificación manual |
| `POST` | `/api/calificaciones/import/preview` | `calificaciones:importar` | Parsear archivo, retornar preview (no persiste) |
| `POST` | `/api/calificaciones/import/confirm` | `calificaciones:importar` | Persistir rows del preview-token |
| `GET` | `/api/umbral-materia` | `calificaciones:ver` | Listar umbrales (filter by materia) |
| `POST` | `/api/umbral-materia` | `calificaciones:importar` | Crear umbral |
| `PUT` | `/api/umbral-materia/{id}` | `calificaciones:importar` | Actualizar umbral |

## Risks / Trade-offs

- **[Risk]** JSONB nota makes SQL aggregation queries harder (sum, avg) → **Mitigation**: Add a computed `nota_numerica` virtual column via a SQL expression for common cases; complex analytics pushed to a read replica.
- **[Risk]** Preview token expires → **Mitigation**: 15-minute TTL, single-use (deleted on confirm).
- **[Risk]** Import of large files blocks workers → **Mitigation**: Streaming parse, batch insert (100 rows/transaction).

## Migration Plan

1. New Alembic migration: create `calificacion` table + `umbral_materia` table
2. Seed default `UmbralMateria` (umbral_pct=60, conjunto_aprobado=["A","B+","C","7","8","9","10"]) for existing materias
3. Deploy application
4. Run import flow with real LMS data