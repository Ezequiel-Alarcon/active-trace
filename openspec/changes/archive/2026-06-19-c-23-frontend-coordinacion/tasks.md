## 1. Shell — Sidebar y rutas de coordinación

- [x] 1.1 Agregar ítems de navegación de coordinación en `AppLayout.tsx` con sección "Coordinación" y sub-ítems (Equipos, Avisos, Tareas, Monitor, Encuentros, Coloquios, Setup), cada uno filtrado por `hasPermission()`
- [x] 1.2 Registrar rutas protegidas en `router.tsx` con `React.lazy` para cada página de coordinación bajo `/coordinacion/*`, con guard `RequirePermission` por permiso específico
- [x] 1.3 Agregar redirect de `/coordinacion` → `/coordinacion/equipos`

## 2. Feature Module — Equipos Docentes

- [x] 2.1 Crear estructura `features/equipos/{components,hooks,services,types,pages}` con barrel exports
- [x] 2.2 Definir tipos TypeScript en `types/equipos.ts` (AsignacionResponse, AsignacionMasivaRequest, CloneRequest, etc.)
- [x] 2.3 Implementar `services/equiposApi.ts` con todos los endpoints: mis-equipos, asignación masiva, clonar, vigencia, exportar
- [x] 2.4 Implementar hooks TanStack Query en `hooks/` (useMisEquipos, useAsignacionMasiva, useClonarEquipo, useVigenciaEquipo, useExportarEquipo)
- [x] 2.5 Implementar página `EquiposPage` con tabs (Mis Equipos / Asignación Masiva / Clonar / Vigencia)
- [x] 2.6 Implementar componente `TablaEquipos` con DataTable y StatusBadge, y `FiltrosEquipos` con FilterBar
- [x] 2.7 Implementar formulario `FormAsignacionMasiva` multi-paso (seleccionar docentes → materia/carrera/cohorte → rol → vigencia → confirmar)
- [x] 2.8 Implementar formulario `FormClonarEquipo` (seleccionar origen → destino → confirmar)
- [x] 2.9 Implementar `FormVigenciaEquipo` con DatePicker para fechas desde/hasta
- [x] 2.10 Implementar botón de exportación con descarga de archivo
- [x] 2.11 Escribir tests de componente: TablaEquipos, FormAsignacionMasiva, FormClonarEquipo

## 3. Feature Module — Avisos

- [x] 3.1 Crear estructura `features/avisos/{components,hooks,services,types,pages}`
- [x] 3.2 Definir tipos en `types/avisos.ts` (AvisoResponse, AvisoCreate, Alcance, Severidad, etc.)
- [x] 3.3 Implementar `services/avisosApi.ts` con GET listado, POST crear, PUT editar, DELETE eliminar
- [x] 3.4 Implementar hooks (useAvisos, useCrearAviso, useEditarAviso, useEliminarAviso)
- [x] 3.5 Implementar página `AvisosPage` con DataTable + botón "Nuevo aviso"
- [x] 3.6 Implementar componente `FormAviso` con React Hook Form + Zod: alcance (select), contexto condicional, severidad, título, cuerpo (textarea enriquecido), vigencia (fecha inicio/fin), requiere ACK (checkbox), estado activo/inactivo
- [x] 3.7 Implementar filtros por alcance, severidad, estado, rango de fechas
- [x] 3.8 Escribir tests: ABM avisos, validación de formulario, filtros

## 4. Feature Module — Tareas Internas

- [x] 4.1 Crear estructura `features/tareas/{components,hooks,services,types,pages}`
- [x] 4.2 Definir tipos en `types/tareas.ts` (TareaResponse, TareaEstado, ComentarioResponse, etc.)
- [x] 4.3 Implementar `services/tareasApi.ts` (listar, cambiar estado, comentarios, delegar)
- [x] 4.4 Implementar hooks (useTareas, useCambiarEstado, useComentarios, useDelegarTarea)
- [x] 4.5 Implementar página `TareasPage` con DataTable global + FilterBar (estado, materia, docente)
- [x] 4.6 Implementar acciones de fila: cambiar estado (dropdown con estados válidos), ver detalle
- [x] 4.7 Implementar modal/vista de detalle con hilo de comentarios y formulario de nuevo comentario
- [x] 4.8 Implementar acción de delegación con selector de docente
- [x] 4.9 Escribir tests: tabla con filtros, cambio de estado, comentarios, delegación

## 5. Feature Module — Monitores Transversales

- [x] 5.1 Extender `features/monitor/` con página `MonitorGeneralPage` (F2.7)
- [x] 5.2 Agregar tipos para monitor general en `features/monitor/types/monitor.ts` (extender existente)
- [x] 5.3 Implementar `services/monitorApi.ts` con fetchMonitorGeneral (C-11)
- [x] 5.4 Implementar hook `useMonitorGeneral` con filtros
- [x] 5.5 Implementar componente `MonitorGeneral` con FilterBar (materia, regional, comisión, búsqueda, estado) + DataTable + botón Exportar
- [x] 5.6 Extender `MonitorSeguimiento` existente con filtro de rango de fechas (F2.9)
- [x] 5.7 Escribir tests: monitor general con filtros, monitor seguimiento con fechas

## 6. Feature Module — Encuentros Admin

- [x] 6.1 Crear estructura `features/encuentros/{components,hooks,services,types,pages}`
- [x] 6.2 Definir tipos en `types/encuentros.ts` (SlotResponse, InstanciaResponse, GuardiaResponse)
- [x] 6.3 Implementar `services/encuentrosApi.ts` (listar slots, instancias, guardias, exportar)
- [x] 6.4 Implementar hooks (useEncuentros, useSlots, useGuardias)
- [x] 6.5 Implementar página `EncuentrosPage` con tabs (Encuentros / Slots / Guardias)
- [x] 6.6 Implementar tabla de encuentros transversal con filtros
- [x] 6.7 Implementar tabla de guardias con filtro de fechas y exportación
- [x] 6.8 Escribir tests: tabla encuentros, filtros, exportación

## 7. Feature Module — Coloquios Admin

- [x] 7.1 Crear estructura `features/coloquios/{components,hooks,services,types,pages}`
- [x] 7.2 Definir tipos en `types/coloquios.ts` (ConvocatoriaResponse, ReservaResponse, MetricasResponse)
- [x] 7.3 Implementar `services/coloquiosApi.ts` (métricas, convocatorias CRUD, reservas)
- [x] 7.4 Implementar hooks (useMetricasColoquios, useConvocatorias, useCrearConvocatoria, useReservas)
- [x] 7.5 Implementar página `ColoquiosPage` con KpiCards de métricas + DataTable de convocatorias
- [x] 7.6 Implementar `FormConvocatoria` con selección de materia, instancia, días/cupos
- [x] 7.7 Implementar vista de agenda de reservas activas por convocatoria
- [x] 7.8 Escribir tests: panel métricas, ABM convocatorias, agenda reservas

## 8. Feature Module — Setup de Cuatrimestre (FL-03)

- [x] 8.1 Crear estructura `features/setup-cuatrimestre/{components,hooks,services,types,pages}`
- [x] 8.2 Definir tipos del wizard en `types/setup.ts`
- [x] 8.3 Implementar página `SetupPage` con wizard multi-paso usando useReducer
- [x] 8.4 Implementar barra de progreso del wizard (pasos 1-7)
- [x] 8.5 Implementar Step1: Crear cohorte (formulario básico, consumir C-06)
- [x] 8.6 Implementar Step2: Clonar equipo (reutilizar componente de equipos)
- [x] 8.7 Implementar Step3: Ajustar asignaciones (reutilizar asignación masiva)
- [x] 8.8 Implementar Step4: Ajustar vigencias (reutilizar componente de vigencia)
- [x] 8.9 Implementar Step5: Cargar programas (consumir C-17, upload de archivos)
- [x] 8.10 Implementar Step6: Cargar fechas académicas (consumir C-17, formulario de fechas)
- [x] 8.11 Implementar Step7: Publicar aviso de bienvenida (reutilizar FormAviso)
- [x] 8.12 Implementar pantalla de resumen final con todas las operaciones realizadas
- [x] 8.13 Escribir tests: wizard navegación, validación por paso, resumen final

## 9. Tests de integración y verificación

- [x] 9.1 Verificar que todas las rutas nuevas cargan correctamente con React.lazy
- [x] 9.2 Verificar que la navegación del sidebar muestra solo ítems permitidos según permisos mock
- [x] 9.3 Ejecutar suite completa de tests (`npm test`) y verificar 0 fallos
- [x] 9.4 Ejecutar typecheck (`npx tsc --noEmit`) y verificar 0 errores
- [x] 9.5 Verificar que las importaciones siguen el barrel `@/shared/ui`
- [x] 9.6 Verificar que no hay estilos inline ni colores de estado ad-hoc en features/
