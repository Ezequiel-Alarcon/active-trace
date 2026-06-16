## Context

C-21 dejó el shell de la SPA: `AuthProvider`, `RequireAuth`, `RequirePermission`, `AppLayout`, `tokenStore` y `apiClient` con refresh transparente, todo bajo `frontend/src/` con estructura feature-based y tests con MSW (`src/test/server.ts`, `setup.ts`). El backend del camino crítico ya existe y está archivado: C-10 (calificaciones-y-umbral), C-11 (analisis-atrasados-reportes) y C-12 (comunicaciones-cola-worker). Esta feature es la primera capa de UI sobre ese backend para los roles docentes y NO toca backend: solo consume API existente. Governance: BAJO (pages frontend sin lógica crítica) → autonomía si pasan los tests. El `router.tsx` actual tiene `TODO: (FEAT) C-22` marcando dónde enganchar las rutas.

## Goals / Non-Goals

**Goals:**
- Exponer el flujo FL-02 completo (importar → preview/selección → umbral → análisis → entregas sin corregir) y FL-04 parte A/C (comunicar a atrasados + tracking) en la SPA.
- Un módulo feature-based por capability, consumiendo los endpoints de C-10/C-11/C-12 vía hooks de TanStack Query sobre `apiClient`.
- Tracking de estados de comunicación en tiempo real mediante polling con corte en estados terminales.
- Tests de componentes/integración con MSW (mock de la red HTTP, no de la lógica) cubriendo import flow, tabla de atrasados, preview de comunicación y transición de estados.

**Non-Goals:**
- Aprobación de envíos masivos (FL-04 parte B, `comunicacion:aprobar`) → es coordinación, va en C-23.
- Monitores transversales de coordinación/admin (F2.7, F2.9) y vistas globales → C-23.
- Cualquier endpoint nuevo de backend: contratos congelados, solo consumo.
- WebSockets/SSE para el tracking: se resuelve con polling (decisión abajo).

## Decisions

**1. Módulos feature-based, uno por capability.** Se crean `features/{comision,calificaciones,analisis,entregas,comunicacion,monitor}/` cada uno con `components/ hooks/ services/ types/ pages/`, espejando la convención ya establecida por `features/auth/`. Alternativa descartada: un único módulo `comision` monolítico → violaría el límite de archivos y mezclaría responsabilidades de import, análisis y comunicación.

**2. Todo fetch pasa por hooks de TanStack Query sobre `apiClient`.** Los `services/*Api.ts` arman las llamadas Axios sobre `@/shared/services/api`; los componentes nunca llaman a la red directo. Reaprovecha el refresh transparente y el manejo 401/403 de C-21. Coherente con la regla dura "todo fetch pasa por hooks de services/".

**3. Tracking de estados por polling con `refetchInterval`.** El hook de tracking usa `useQuery` con `refetchInterval` que se desactiva (retorna `false`) cuando todos los mensajes del lote están en estado terminal (OK/Fallido/Cancelado). Alternativa descartada: WebSocket/SSE → el backend de C-12 expone estado por endpoint REST, no hay canal push; polling es suficiente para el volumen docente y mantiene el contrato congelado. Trade-off: latencia de hasta un intervalo; aceptable para seguimiento de cola.

**4. Formularios con React Hook Form + Zod.** El umbral (0–100, default 60) y los filtros del monitor se validan con esquemas Zod tipados antes de enviarse. Sin `any`, sin class components, componentes PascalCase < 200 LOC.

**5. Selección de comisión como estado de feature, no global.** La materia/cohorte activa vive en el árbol de la feature (context o estado de la página `comision`), y se pasa como parámetro a los hooks de query (forma parte de la `queryKey`). No se agrega store global: el alcance real de datos lo impone el backend desde la sesión; el selector solo elige entre lo permitido.

**6. Estados vacíos explícitos como requisito de UI.** Atrasados, ranking, notas finales, reportes, entregas y monitor renderizan un estado vacío informativo cuando no hay datos/actividades — es comportamiento especificado (RN, F2.4), no decorativo. Se implementa como componente compartido dentro de cada feature o en `shared/components` si se repite.

**7. Tests con MSW, sin mockear lógica.** Se extiende `src/test/server.ts` con handlers para los endpoints de C-10/C-11/C-12. Se testea render + interacción + transición de estados (el polling se ejercita avanzando el handler entre refetches). Mockear la red HTTP es válido en frontend; lo prohibido es mockear la DB en backend (no aplica aquí).

## Risks / Trade-offs

- **Contratos de API de C-10/C-11/C-12 no verificados en código** → Mitigación: antes de implementar cada `service`, leer los specs/routers archivados de esos changes para fijar shapes de request/response; registrar discrepancias como `TODO: (REVIEW)` en el service y surfacearlas, no inventar el contrato.
- **Polling puede multiplicar requests con lotes grandes** → Mitigación: un solo query por lote (no por mensaje), `refetchInterval` razonable (p. ej. 3–5s) y corte inmediato al alcanzar estados terminales.
- **El upload de archivos (calificaciones, finalización) puede no encajar con el `apiClient` JSON por defecto** → Mitigación: usar `multipart/form-data` explícito en el service; verificar que el interceptor de auth/refresh no rompa el body binario.
- **Estados vacíos vs. errores de red se pueden confundir** → Mitigación: distinguir en el hook `isError` (mensaje del backend) de "sin datos" (estado vacío informativo); son ramas de UI separadas.

## Open Questions

- **Shapes exactos de los endpoints de C-10/C-11/C-12**: se resuelven leyendo los changes archivados durante el apply de cada service; no bloquean la propuesta pero deben confirmarse antes de codear cada hook.
- **Intervalo de polling y timeout máximo del tracking**: valor concreto (3s/5s) y si hay corte por tiempo además del corte por estado terminal — decidir en apply según el comportamiento del worker de C-12.
- **Endpoint y formato del export de entregas sin corregir**: si el backend devuelve el archivo (blob) o el front lo arma desde el JSON — confirmar contra C-11 antes de implementar la acción de export.
