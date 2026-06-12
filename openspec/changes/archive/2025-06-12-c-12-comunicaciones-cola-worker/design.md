## Context

El modelo E21 (Comunicacion) ya existe con los estados Pendiente→Enviando→Enviado/Error/Cancelado. C-11 (RBAC) proporciona el sistema de permisos `comunicacion:enviar` y `comunicacion:aprobar`. El worker aún no existe: los mensajes quedan en Pendiente indefinidamente.

## Goals / Non-Goals

**Goals:**
- Worker async que consuma mensajes Pendiente y los transicione al estado final (Enviado/Error/Cancelado)
- Preview obligatorio antes de encolar (RN-16)
- Aprobación configurable por tenant para envíos masivos (RN-17)
- Audit trail completo con código COMUNICACION_ENVIAR

**Non-Goals:**
- No implementar el motor de envío real (N8N/externo) — solo la interfaz de dispatch
- No implementar templates de mensajes — solo preview del cuerpo existente

## Decisions

### D1: Worker como tarea background独立的
**Decision**: El worker corre como proceso independiente (no dentro del request HTTP).
**Rationale**: Los envíos pueden ser lentos y retries deben sobrevivir restarts del API.
**Alternatives**: BackgroundTasks de FastAPI — no survive restarts, acopla worker a API process.

### D2: Polling con lock competitivo
**Decision**: El worker hace polling con `SELECT FOR UPDATE SKIP LOCKED` sobre mensajes Pendiente.
**Rationale**: Permite múltiples workers sin coordinación externa. Simple y tolerante a fallos.
**Alternatives**: Redis Streams / RabbitMQ — añade dependencia externa; polling es suficiente para volúmenes esperados.

### D3: Transición de estados en el worker
**Decision**: El worker hace la transición Pendiente → Enviando (antes de dispatch) y luego Enviando → Enviado/Error (post dispatch).
**Rationale**: Garantiza que un mensaje no sea procesado dos veces. El lock preventivo ya existe.

### D4: Preview sin persistencia
**Decision**: El endpoint de preview toma el cuerpo del mensaje y lo renderiza sin guardarlo en la DB.
**Rationale**: El preview es solo para confirmación antes del envío real. No necesita estado intermedio.

### D5: Aprobación por lote
**Decision**: La aprobación opera a nivel de `lote_id`, no por mensaje individual.
**Rationale**: FL-04 indica aprobación de "lote completo". La aprobación individual es una extensión futura.

## Risks / Trade-offs

- **[Risk] Mensaje bloqueado permanentemente**: Si el worker crash durante Enviando, el mensaje queda huérfano.
  - **Mitigation**: Job recovery que resetea Enviando → Pendiente tras timeout (ej: 5 min sin actualización).

- **[Risk] Aprobación obligatoria pero sin reviewer disponible**: Mensajes Pendiente nunca se procesan.
  - **Mitigation**: Threshold configurable por tenant (ej: solo requiere aprobación si destinatarios > 10).

- **[Risk] Worker no levanta si la DB no está lista**: Start-up failure.
  - **Mitigation**: Retry con backoff exponencial en la conexión, max 5 intentos.