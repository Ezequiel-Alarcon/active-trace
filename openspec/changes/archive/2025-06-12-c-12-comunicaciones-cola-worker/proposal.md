## Why

El sistema necesita un worker asincrónico que consuma la cola de comunicaciones (E21) y transicione los mensajes entre estados (RN-15). Sin este worker, los mensajes permanecen en Pendiente indefinidamente. El flujo completo (FL-02 pasos 7-8, FL-04) requiere preview obligatorio (RN-16) y aprobación configurable por tenant (RN-17).

## What Changes

- Worker async que consume la cola de comunicaciones y transiciona estados Pendiente → Enviando → Enviado/Error/Cancelado
- Endpoint de preview (`POST /api/comunicaciones/preview`) requerido antes de encolar (RN-16)
- Guard de aprobación `comunicacion:aprobar` configurable por tenant (RN-17)
- Endpoint de aprobación/rechazo de lotes pendientes
- Audit log con código `COMUNICACION_ENVIAR`

## Capabilities

### New Capabilities

- `comunicacion-worker`: Worker async que consume la cola de mensajes, realiza el dispatch real (integración N8N/externa) y actualiza estados. Aplica retry con backoff exponencial en caso de falla.
- `comunicacion-preview`: Endpoint de previsualización que renderiza el mensaje tal como lo recibirá el destinatario, sin encolarlo aún.
- `comunicacion-aprobacion`: Flujo de aprobación/rechazo de envíos masivos antes del dispatch. Configurable por tenant.
- `comunicacion-estados`: Transiciones de estado documentadas y auditadas (Pendiente → Enviando → Enviado/Error/Cancelado).

### Modified Capabilities

- `comunicacion-crud` (existente): extiende con transición de estados y lote_id para agrupar envíos masivos.

## Impact

- Nuevo módulo `app/modules/comunicacion/` con worker, schemas, services, repositories
- Endpoint `POST /api/comunicaciones/preview` (requiere `comunicacion:enviar`)
- Endpoint `POST /api/comunicaciones/lotes/{lote_id}/aprobar` y `rechazar` (requiere `comunicacion:aprobar`)
- Worker consume cola independientemente de requests HTTP
- Integración con sistema de audit log (COMUNICACION_ENVIAR)
- Dependencias: C-11 (RBAC), modelo Comunicacion existente (E21)