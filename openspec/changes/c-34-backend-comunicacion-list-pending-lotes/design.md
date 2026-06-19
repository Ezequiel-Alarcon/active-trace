## Context

The `AprobacionesPage` frontend needs to display a list of all pending communication batches for the current tenant. It calls `fetchLotesPendientes()` → `GET /api/comunicaciones/lotes?estado=Pendiente`. The endpoint does not exist.

Current state:
- `GET /api/comunicaciones/lotes/{lote_id}` returns `LoteStatusResponse` for a single batch ✅
- `POST /api/comunicaciones/lotes/{lote_id}/aprobar` ✅
- `POST /api/comunicaciones/lotes/{lote_id}/rechazar` ✅
- `GET /api/comunicaciones/lotes` (list with filter) ❌ MISSING

The `ComunicacionRepository` has `count_by_lote_and_estado(lote_id)` but lacks a method to list all lotes grouped by `lote_id` with aggregated counts and metadata (asunto, cuerpo, solicitado_por_nombre, destinatarios).

## Goals / Non-Goals

**Goals:**
- Add `GET /api/comunicaciones/lotes?estado=<estado>` endpoint returning `LotePendienteResponse[]`
- Multi-tenant: results scoped to `current_user.tenant_id`
- Permission: `comunicacion:aprobar`
- Grouped aggregation by `lote_id` with status counts per batch

**Non-Goals:**
- Modifying existing single-lote endpoints
- Pagination (not required by C-32)
- Ordering beyond `ORDER BY created_at DESC`

## Decisions

### 1. New repository method: `list_lotes_grouped(tenant_id, estado=None)`

Uses a single SQL query with `GROUP BY lote_id` to aggregate counts per status and collect metadata (asunto, cuerpo, solicitados_por, destinatarios). Returns a list of aggregated lote rows.

**Alternative considered**: Fetch all `Comunicacion` records for tenant, then group in Python. Rejected — O(n) memory, no DB-level aggregation.

### 2. New Pydantic schema: `LotePendienteResponse`

Fields match frontend expectations: `lote_id`, `tenant_id`, `total`, `pendientes`, `enviando`, `enviados`, `errores`, `cancelados`, `asunto`, `cuerpo`, `solicitado_por_nombre`, `destinatarios: list[str]`.

### 3. Router endpoint: `GET /api/comunicaciones/lotes`

Registered at `prefix="/api/comunicaciones"` as `/lotes`. Query param `estado` is optional — maps `Pendiente` → `ComunicacionEstado.PENDIENTE`. When omitted, returns all lotes regardless of estado.

### 4. `solicitado_por_nombre` aggregation

Collected from `solicitado_por` field on `Comunicacion` — using the first non-null value found within the group.

## Risks / Trade-offs

- [Risk] Large number of lotes per tenant could return many rows → **Mitigation**: This is a management/approval screen; scale is bounded by human review capacity. Add pagination later if needed.
- [Risk] `destinatarios: list[str]` could grow large per batch → **Mitigation**: Cap at reasonable limit (e.g., 100) or return top-N + `"and N more"`. For now, return all — batch sizes are controlled by RN-16 threshold.