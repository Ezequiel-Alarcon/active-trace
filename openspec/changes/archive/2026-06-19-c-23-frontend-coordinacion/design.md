## Context

Este change construye la capa de presentación para los roles COORDINADOR y ADMIN sobre las APIs backend ya implementadas (C-08 equipos, C-13 encuentros, C-14 coloquios, C-15 avisos, C-16 tareas, C-17 programas/fechas, C-11 monitores). El frontend actual (C-21 + C-22) ya tiene el shell, auth flow, ruteo por permiso y los módulos académicos del PROFESOR. Sigue feature-based modules en `frontend/src/features/{nombre}/`, TanStack Query para server state, React Hook Form + Zod para formularios, y la capa `@/shared/ui` para primitivos visuales.

## Goals / Non-Goals

**Goals:**
- 7 feature modules nuevos con estructura `{components,hooks,services,types,pages}` completa.
- Navegación en sidebar agrupada en sección "Coordinación" visible solo para COORDINADOR/ADMIN.
- Cada página consume su API backend existente mediante hooks TanStack Query.
- Cada feature incluye loading, empty y error states.
- Cobertura de tests ≥80% líneas sobre componentes críticos (ABM, workflows multi-paso).
- El flujo FL-03 (Setup de cuatrimestre) se implementa como wizard multi-paso guiado.

**Non-Goals:**
- No se modifican APIs backend — solo consumo REST existente.
- No se implementan nuevas funcionalidades de dominio no documentadas en la KB.
- No se re-estilan páginas existentes (C-22) — solo se agregan las de coordinación.
- No se implementa la bandeja de mensajería interna (C-20) ni el panel de auditoría (C-19) — esos son C-24.

## Decisions

1. **Estructura de 7 feature modules independientes**: Cada subsistema (equipos, avisos, tareas, monitores, encuentros, coloquios, setup) es un feature module independiente. Esto mantiene <200 LOC por archivo, facilita el testing aislado y permite lazy-loading futuro. Las dependencias entre módulos se resuelven por composición (ej. el wizard de setup importa componentes de equipos/avisos/programas).

2. **Páginas lazy-loaded con React.lazy**: Las páginas de coordinación no se cargan hasta que el usuario navega a ellas. Las rutas se registran en el router con `React.lazy(() => import(...))`.

3. **Sidebar con sección agrupada**: Se agrega una sección "Coordinación" colapsable/expandible en `AppLayout` con sub-ítems para Equipos, Avisos, Tareas, Encuentros, Coloquios, Setup. Cada ítem se filtra por `hasPermission()` (fail-closed).

4. **Wizard de Setup de Cuatrimestre multi-paso con estado local**: El wizard FL-03 se implementa como un solo page component que maneja un paso actual en estado React (useReducer para pasos ramificados). Cada paso es un sub-componente importado de los módulos respectivos (equipos → clonar, avisos → crear). El wizard tiene una barra de progreso y botones Anterior/Siguiente/Finalizar.

5. **Consumo directo de API existentes via TanStack Query**: Cada service llama al `apiClient` de `@/shared/services/api`. No se agrega capa de abstracción adicional — los hooks de TanStack Query son la capa de server state. Las mutaciones usan `useMutation` con `onSuccess` para invalidar queries relacionadas.

6. **Formularios con React Hook Form + Zod**: Todo formulario ABM (avisos, tareas, coloquios) usa `useForm` + schema Zod, con `TextField` de `@/shared/ui` para inputs. Para formularios complejos (asignación masiva, convocatoria de coloquio) se usan sub-formularios paso a paso.

## Risks / Trade-offs

- [Risk] 7 feature modules en un solo change → archivos tocados (~80-100). **Mitigación**: división por tasks atómicas (1 task por módulo, ordenadas por dependencia). Cada task es un commit granular.
- [Risk] El wizard de setup multi-paso puede crecer a >200 LOC. **Mitigación**: cada paso es un componente separado en `features/setup-cuatrimestre/components/Step*.tsx`.
- [Risk] Las APIs de backend pueden tener inconsistencias de respuesta. **Mitigación**: tipar todos los responses en `types/*.ts` y testear contra datos mock que reflejen la estructura real.
- [Trade-off] React.lazy evita cargar código no usado pero agrega un pequeño delay de carga. Aceptable para rutas de coordinación de uso menos frecuente que el workspace del profesor.
