## Why

The frontend `AprobacionesPage` (C-32 archived) requires `GET /api/comunicaciones/lotes?estado=Pendiente` to fetch all pending communication batches awaiting approval for the current tenant. This endpoint does not exist — only `GET /api/comunicaciones/lotes/{lote_id}` exists, which returns a single batch by ID. Without this endpoint, the approval UI cannot display the list of pending batches.

## What Changes

- **New endpoint**: `GET /api/comunicaciones/lotes?estado=<estado>` — lists all batches for the tenant, optionally filtered by estado (Pendiente, Enviando, etc.)
- **New repository method**: `get_lotes_pendientes(tenant_id)` — aggregatesComunicacion records grouped by `lote_id`, returning counts per status and metadata
- **New Pydantic schema**: `LotePendienteResponse` with fields: `lote_id`, `tenant_id`, `total`, `pendientes`, `enviando`, `enviados`, `errores`, `cancelados`, `asunto`, `cuerpo`, `solicitado_por_nombre`, `destinatarios: string[]`
- **New permission check**: `comunicacion:aprobar` required on the list endpoint

## Capabilities

### New Capabilities

- `comunicacion-list-pending-lotes`: Returns aggregated batch status grouped by `lote_id` for a tenant, filtered by optional `estado` query param. Requires `comunicacion:aprobar` permission.

### Modified Capabilities

- (none)

## Impact

- **Backend**: New route in `app/modules/comunicacion/router.py`, new method in `ComunicacionRepository`
- **API**: New REST endpoint `GET /api/comunicaciones/lotes?estado=Pendiente`
- **Schema**: New `LotePendienteResponse` Pydantic model in `app/modules/comunicacion/schemas.py`
- **Tests**: Unit tests for repository aggregation, integration tests for endpoint