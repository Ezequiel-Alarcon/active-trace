## Context

El backend de C-12 implementó la cola de comunicaciones con estados (Pendiente → Enviado / Fallido / Cancelado) y los endpoints de approve/reject en `POST /api/comunicaciones/lotes/{lote_id}/aprobar` y `POST /api/comunicaciones/lotes/{lote_id}/rechazar`. El frontend existente en `features/comunicacion/` tiene la UI de envío (F3.2) pero NO la UI de aprobación (F3.3).

La UI de aprobación es necesaria para que los COORDINADOR/ADMIN puedan consumir la cola Pendiente. Sin ella, los mensajes nunca avanzan.

## Goals / Non-Goals

**Goals:**
- Permitir a COORDINADOR/ADMIN ver todos los lotes en estado Pendiente
- Mostrar detalle del lote (asunto, cuerpo, destinatarios) antes de decidir
- Aprobar o rechazar lotes con feedback visual de resultado
- Proteger la ruta con permiso `comunicacion:aprobar`

**Non-Goals:**
- No se implementa lógica de umbral de aprobación (ya existe en backend via `tenant.umbral_aprobacion`)
- No se modifica el flujo de envío (F3.2) — eso ya existe
- No se re-implementan los endpoints de backend (ya existen en C-12)

## Decisions

### Patrón de página: tabla + modal de detalle
Se sigue el patrón existente en `TareasPage.tsx`: tabla con filas clickeables que abren un modal de detalle, con acciones de approve/reject dentro del modal.

**Alternativa descartada**: inline actions en la tabla (ocupa mucho espacio, menos contexto antes de decidir).

### Routing: `/comision/aprobaciones` con RequirePermission
Se crea una nueva ruta en `shared/router.tsx` bajo el layout de comisiones. Se usa `RequirePermission` para filtrar acceso.

**Decisión**: no crear un nuevo layout, reutilizar la estructura de comisiones existente.

### API service: `comunicacionApi.ts` existente + extensión
Se extiende `comunicacionApi.ts` con `fetchLotesPendientes` (GET con filtro estado=Pendiente) y las funciones de approve/reject. No se crea archivo nuevo.

### Tipado: extensión de `comunicacion.ts`
Se extiende `LoteStatusResponse` con campos adicionales que el endpoint de detalle devuelve (`asunto`, `cuerpo`, `destinatarios` preview). El tipo `LotePendienteResponse` se agrega al types file.

## Risks / Trade-offs

- [Risk] Si el backend no devuelve `destinatarios` en el detalle del lote, el modal solo mostrará asunto/cuerpo sin poder listar recipients. → Mitigation: el modal mostrará lo que tenga disponible; si no hay destinatarios, se muestra "Ver contenido completo" con el cuerpo completo.
- [Risk] Sin paginación en el listado de lotes, si hay muchos pendientes la tabla puede crecer mucho. → Mitigation: la tabla usa paginación del DataTable existente; si no, se agrega limit/offset en follow-up.
- [Trade-off] Approve/Reject son operaciones irreversibles en la práctica (el mensaje pasa a cola de envío). Se muestra confirmación antes de ejecutar.