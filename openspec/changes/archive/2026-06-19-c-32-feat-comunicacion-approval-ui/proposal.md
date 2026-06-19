## Why

Los envíos masivos de comunicaciones (F3.2) que superen el umbral de aprobación configurable del tenant quedan en estado Pendiente. El backend ya tiene los endpoints de approve/reject (C-12 archivado) pero el frontend no expone UI para que un COORDINADOR o ADMIN revise y apruebe/rechace esos lotes. Sin esta UI, los mensajes nunca avanzan de la cola — la funcionalidad de aprobación queda incompleta.

## What Changes

- Nueva página `AprobacionesPage` en `features/comunicacion/pages/` con tabla de lotes pendientes
- Hook `useLotesPendientes()` — fetches `GET /api/comunicaciones/lotes` filtrado por estado Pendiente
- Hook `useAprobarLote()` — POST a `POST /api/comunicaciones/lotes/{lote_id}/aprobar`
- Hook `useRechazarLote()` — POST a `POST /api/comunicaciones/lotes/{lote_id}/rechazar`
- Modal de detalle (`DetalleLoteModal`) — muestra asunto, cuerpo, lista de destinatarios preview antes de decidir
- Permission guard: `comunicacion:aprobar` visible solo para COORDINADOR y ADMIN
- Ruteo en `shared/router.tsx` con guard de permiso
- API service `fetchLotesPendientes` en `comunicacionApi.ts`

## Capabilities

### New Capabilities
- `comunicacion-approval`: UI de revisión y aprobación/rechazo de lotes de comunicaciones pendientes. Incluye listado de lotes, modal de detalle, y acciones de approve/reject con feedback de estado.

## Impact

- **Frontend**: nueva feature `features/comunicacion/`, página `AprobacionesPage`, hooks, modal, route guard
- **Backend**: no se modifica — usa endpoints existentes de C-12
- **Dependencias**: C-12 (backend de approve/reject existe), C-21 (frontend shell y auth existe), C-22 (komunikations existente)