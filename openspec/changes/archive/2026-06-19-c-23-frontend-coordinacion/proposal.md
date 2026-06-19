## Why

Los roles COORDINADOR y ADMIN necesitan una interfaz de gestión para operar el ciclo académico completo: configurar equipos docentes, publicar avisos, supervisar tareas internas, administrar encuentros y coloquios, monitorear alumnos de forma transversal y ejecutar el setup de cuatrimestre. El backend ya expone las APIs de los módulos C-08, C-13, C-14, C-15, C-16 y C-17; falta la capa de presentación.

## What Changes

- Nuevos feature modules frontend en `frontend/src/features/` para los 7 subsistemas de coordinación/admin, cada uno con su estructura `{components,hooks,services,types,pages}`.
- Nuevas rutas protegidas por permiso en el shell (`AppLayout` + sidebar) agrupadas bajo secciones de coordinación.
- Nueva navegación: sección "Coordinación" en el sidebar con sub-entradas visibles según permisos.
- Hooks TanStack Query para cada API backend existente.
- Tests de componente e integración (Vitest + RTL) para cada feature, siguiendo los patrones existentes.
- Las páginas y componentes se construyen sobre los primitivos de `@/shared/ui` (DataTable, StatusBadge, PageHeader, FilterBar, KpiCard, etc.) — cero estilos ad-hoc.

## Capabilities

### New Capabilities
- `frontend-equipos-docentes` — Mis equipos (vista del usuario autenticado), asignación masiva, clonar entre períodos, modificar vigencia general, exportar equipo. Consume C-08.
- `frontend-avisos` — ABM de avisos con scope (Global/PorMateria/PorCohorte/PorRol), severidad, vigencia, flag de ACK obligatorio. Consume C-15.
- `frontend-tareas-internas` — Vista global de tareas con workflow (Pendiente→En progreso→Resuelta→Cancelada), comentarios en hilo, delegación. Consume C-16.
- `frontend-monitores-transversales` — Monitor general de actividades (F2.7) y monitor con rango de fechas (F2.9). Consume C-11.
- `frontend-encuentros-admin` — Vista transversal de slots e instancias, registro y exportación de guardias. Consume C-13.
- `frontend-coloquios-admin` — Convocatorias (creación y listado), reservas activas, resultados, panel de métricas. Consume C-14.
- `frontend-setup-cuatrimestre` — Flujo guiado multi-paso para FL-03: crear cohorte, clonar equipo, ajustar asignaciones, cargar programas y fechas, publicar aviso de bienvenida. Consume C-06, C-08, C-15, C-17.

### Modified Capabilities
- `frontend-app-shell` — El shell existente (AppLayout + router) se modifica para agregar las nuevas rutas de coordinación y la navegación en el sidebar.
- `frontend-design-system` — Se extiende con nuevos estados semánticos si los primitivos actuales no cubren algún estado de dominio de estas features.

## Impact

- `frontend/src/features/equipos/` — nuevo feature module
- `frontend/src/features/avisos/` — nuevo feature module
- `frontend/src/features/tareas/` — nuevo feature module
- `frontend/src/features/monitor/` — extendido con vistas F2.7 y F2.9 (ya existe `MonitorSeguimiento` para F2.8)
- `frontend/src/features/encuentros/` — nuevo feature module
- `frontend/src/features/coloquios/` — nuevo feature module
- `frontend/src/features/setup-cuatrimestre/` — nuevo feature module
- `frontend/src/shared/components/AppLayout.tsx` — agregar ítems de navegación de coordinación
- `frontend/src/shared/router.tsx` — registrar nuevas rutas protegidas
- `frontend/src/shared/ui/` — posible extensión de `EstadoSemantico` si se necesitan nuevos colores
