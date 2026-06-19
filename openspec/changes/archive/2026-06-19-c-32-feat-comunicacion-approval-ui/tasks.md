## 1. Types y API Service

- [x] 1.1 Add `LotePendienteResponse` type to `features/comunicacion/types/comunicacion.ts` (extend LoteStatusResponse with `asunto`, `cuerpo`, `solicitado_por_nombre`, `destinatarios: string[]`)
- [x] 1.2 Add `fetchLotesPendientes()` to `features/comunicacion/services/comunicacionApi.ts` (GET `/api/comunicaciones/lotes` with `estado=Pendiente` filter)
- [x] 1.3 Add `aprobarLote(loteId: string)` and `rechazarLote(loteId: string)` to `comunicacionApi.ts`
- [x] 1.4 Add `useLotesPendientes()` hook in `features/comunicacion/hooks/useComunicacion.ts`

## 2. Componentes

- [x] 2.1 Create `features/comunicacion/components/DetalleLoteModal.tsx` — modal with full lote data, approve/reject buttons, confirmation dialogs
- [x] 2.2 Create `features/comunicacion/hooks/useAprobarLote.ts` — mutation hook for approve
- [x] 2.3 Create `features/comunicacion/hooks/useRechazarLote.ts` — mutation hook for reject

## 3. Página

- [x] 3.1 Create `features/comunicacion/pages/AprobacionesPage.tsx` — table of pending lotes with "Ver" action, EmptyState, loading/error states
- [x] 3.2 Add route `/comision/aprobaciones` in `shared/router.tsx` with `RequirePermission permission="comunicacion:aprobar"`
- [x] 3.3 Add navigation link in `AppLayout.tsx` under Comunicaciones section (only visible with `comunicacion:aprobar` permission)

## 4. Tests

- [x] 4.1 Write unit tests for `DetalleLoteModal.tsx`
- [x] 4.2 Write unit tests for `AprobacionesPage.tsx`
- [x] 4.3 Write unit tests for `useAprobarLote` and `useRechazarLote` hooks
- [x] 4.4 Add mock handlers in `src/test/server.ts` for approve/reject endpoints

## 5. Integración y Validación

- [x] 5.1 Run `npm run lint` and fix any issues
- [x] 5.2 Verify all new files follow project conventions (PascalCase components, snake_case APIs, no `any`)