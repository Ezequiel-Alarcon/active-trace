## 1. Domain Model & Schemas

- [ ] 1.1 Create `app/modules/comunicacion/models/comunicacion.py` with SQLAlchemy model (states enum, state machine guards)
- [ ] 1.2 Create `app/modules/comunicacion/schemas/comunicacion.py` with Pydantic DTOs (Create, Update, Response, StateTransition)
- [ ] 1.3 Create `app/modules/comunicacion/schemas/preview.py` with PreviewRequest, PreviewResponse
- [ ] 1.4 Create `app/modules/comunicacion/schemas/lote.py` with LoteAprobarRequest, LoteRechazarRequest
- [ ] 1.5 Add alembic migration for Comunicacion table (already exists — verify state machine columns)

## 2. Repository Layer

- [ ] 2.1 Create `app/modules/comunicacion/repositories/comunicacion.py` with:
  - `get_pending_messages(limit)` — SELECT FOR UPDATE SKIP LOCKED
  - `get_by_lote_id(lote_id)` — get all messages in a lote
  - `update_estado(id, estado, error_detail=None)` — state transition with audit
  - `get_stuck_sending(timeout_minutes)` — recovery query for stuck Enviando
- [ ] 2.2 Add `require_permission` guards for `comunicacion:enviar` and `comunicacion:aprobar`

## 3. Service Layer

- [ ] 3.1 Create `app/modules/comunicacion/services/dispatch.py` — interface to N8N/external dispatch (abstract base, real impl calls webhook)
- [ ] 3.2 Create `app/modules/comunicacion/services/approval.py` — approval threshold logic per tenant
- [ ] 3.3 Create `app/modules/comunicacion/services/preview.py` — render message preview without persisting

## 4. API Endpoints

- [ ] 4.1 `POST /api/comunicaciones/preview` — preview endpoint (requires `comunicacion:enviar`)
- [ ] 4.2 `POST /api/comunicaciones` — enqueue messages (apply threshold check, create with lote_id)
- [ ] 4.3 `GET /api/comunicaciones/lotes/{lote_id}` — get lote status
- [ ] 4.4 `POST /api/comunicaciones/lotes/{lote_id}/aprobar` — approve lote (requires `comunicacion:aprobar`)
- [ ] 4.5 `POST /api/comunicaciones/lotes/{lote_id}/rechazar` — reject lote (requires `comunicacion:aprobar`)
- [ ] 4.6 `GET /api/comunicaciones/{id}` — get single message status
- [ ] 4.7 Add COMUNICACION_ENVIAR audit log entries on all state transitions

## 5. Worker Implementation

- [ ] 5.1 Create `app/worker/comunicacion_worker.py` — main worker loop with polling
- [ ] 5.2 Implement retry with exponential backoff (max 3 retries)
- [ ] 5.3 Implement recovery job: reset Enviando → Pendiente after 5 min timeout
- [ ] 5.4 Add worker startup with DB connection retry (backoff, max 5 attempts)
- [ ] 5.5 Create `app/worker/__init__.py` and entrypoint script

## 6. Configuration

- [ ] 6.1 Add to `app/config.py`:
  - `COMUNICACION_WORKER_POLL_INTERVAL` (default 5 seconds)
  - `COMUNICACION_WORKER_LOCK_TIMEOUT` (default 5 minutes)
  - `COMUNICACION_DISPATCH_WEBHOOK_URL`
  - `COMUNICACION_APROBACION_THRESHOLD` (default 10)
- [ ] 6.2 Add tenant-level config for `umbral_aprobacion` (per Tenant model)

## 7. Testing

- [ ] 7.1 Unit tests for state machine transitions (valid/invalid)
- [ ] 7.2 Unit tests for approval threshold logic
- [ ] 7.3 Unit tests for dispatch service (mock external call)
- [ ] 7.4 Integration tests for worker polling and lock acquisition
- [ ] 7.5 Integration tests for preview endpoint
- [ ] 7.6 Integration tests for approve/reject endpoints
- [ ] 7.7 Test recovery job resets stuck Enviando messages