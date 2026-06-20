## 1. Repository Layer

- [x] 1.1 Add `list_lotes_grouped(tenant_id, estado=None)` method to `ComunicacionRepository` — aggregates by `lote_id`, returns counts per estado + metadata (`asunto`, `cuerpo`, `destinatarios` list)
- [x] 1.2 Add unit tests for `list_lotes_grouped` covering: all lotes, filtered by estado, empty result, multi-tenant isolation

## 2. Schema Layer

- [x] 2.1 Add `LotePendienteResponse` schema to `app/modules/comunicacion/schemas/comunicacion.py` with fields: `lote_id`, `tenant_id`, `total`, `pendientes`, `enviando`, `enviados`, `errores`, `cancelados`, `asunto`, `cuerpo`, `destinatarios: list[str]`
- [x] 2.2 Add `extra='forbid'` to model_config

## 3. Router Layer

- [x] 3.1 Add `GET /api/comunicaciones/lotes` endpoint to `router.py` with optional `estado` query param, `require_permission("comunicacion:aprobar")`
- [x] 3.2 Map `estado` query string (`Pendiente`, `Enviando`, etc.) to `ComunicacionEstado` enum values
- [x] 3.3 Add integration tests for the new endpoint covering: happy path with pending batches, empty result, 403 without permission
