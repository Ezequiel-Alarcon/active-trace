## ADDED Requirements

### Requirement: List pending communication batches

The system SHALL provide an endpoint `GET /api/comunicaciones/lotes?estado=<estado>` that returns all communication batches for the current tenant, optionally filtered by estado. Each batch SHALL be represented as a `LotePendienteResponse` with aggregated status counts and metadata grouped by `lote_id`.

#### Scenario: List all pending batches without filter

- **WHEN** a user with `comunicacion:aprobar` permission calls `GET /api/comunicaciones/lotes`
- **THEN** the system returns all unique `lote_id` groups for the tenant, each with `total`, `pendientes`, `enviando`, `enviados`, `errores`, `cancelados`, `asunto`, `cuerpo`, `solicitado_por_nombre`, and `destinatarios`

#### Scenario: List pending batches filtered by estado

- **WHEN** a user with `comunicacion:aprobar` permission calls `GET /api/comunicaciones/lotes?estado=Pendiente`
- **THEN** the system returns only batches that have at least one `Comunicacion` in `PENDIENTE` estado
- **AND** each batch includes accurate aggregated counts across all estados

#### Scenario: Empty result when no batches exist

- **WHEN** a user with `comunicacion:aprobar` permission calls `GET /api/comunicaciones/lotes?estado=Pendiente`
- **AND** no pending batches exist for the tenant
- **THEN** the system returns an empty array `[]`

#### Scenario: Rejects request without permission

- **WHEN** a user without `comunicacion:aprobar` permission calls `GET /api/comunicaciones/lotes`
- **THEN** the system returns `403 Forbidden`

### Requirement: LotePendienteResponse schema

The `LotePendienteResponse` schema SHALL contain:

- `lote_id: UUID` — batch identifier
- `tenant_id: UUID` — tenant of the batch
- `total: int` — total number of messages in the batch
- `pendientes: int` — count of PENDIENTE messages
- `enviando: int` — count of ENVIANDO messages
- `enviados: int` — count of ENVIADO messages
- `errores: int` — count of ERROR messages
- `cancelados: int` — count of CANCELADO messages
- `asunto: str` — message subject (from first message in batch)
- `cuerpo: str` — message body (from first message in batch)
- `solicitado_por_nombre: str` — creator name (from first message in batch)
- `destinatarios: list[str]` — list of unique recipient emails in the batch