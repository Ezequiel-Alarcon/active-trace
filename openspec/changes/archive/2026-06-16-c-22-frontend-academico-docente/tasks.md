## 1. Contratos de API y fundaciones de la feature

- [x] 1.1 Leer los changes archivados de C-10 (calificaciones-y-umbral), C-11 (analisis-atrasados-reportes) y C-12 (comunicaciones-cola-worker) y documentar los shapes de request/response de cada endpoint a consumir; marcar discrepancias con `TODO: (REVIEW)`
- [x] 1.2 Crear el árbol de módulos feature-based vacío: `features/{comision,calificaciones,analisis,entregas,comunicacion,monitor}/{components,hooks,services,types,pages}`
- [x] 1.3 Definir los tipos TypeScript compartidos por feature en `types/` a partir de los contratos del paso 1.1 (sin `any`)
- [x] 1.4 Extender `src/test/server.ts` (MSW) con handlers base para los endpoints de C-10/C-11/C-12

## 2. Workspace de comisión (frontend-comision-workspace)

- [x] 2.1 RED+GREEN: hook `useComisionesDisponibles` que lista las comisiones permitidas por la sesión (test con MSW)
- [x] 2.2 RED+GREEN: componente selector de materia/cohorte; estado guía sin selección (test de render + selección)
- [x] 2.3 RED+GREEN: contenedor/página de comisión que conserva la comisión activa al navegar entre vistas (test de cambio de vista)
- [x] 2.4 Registrar rutas en `shared/router.tsx` envueltas en `RequirePermission` (`calificaciones:importar`, `atrasados:ver`, `comunicacion:enviar`) y reemplazar los `TODO: (FEAT) C-22`
- [x] 2.5 RED+GREEN: entradas de menú en `AppLayout` condicionadas por permiso (test: menú oculta lo no permitido)

## 3. Importación de calificaciones (frontend-calificaciones-import)

- [x] 3.1 RED+GREEN: `calificacionesApi` con upload `multipart/form-data` sobre `apiClient`; verificar que auth/refresh no rompe el body binario
- [x] 3.2 RED+GREEN: hook `useImportarCalificaciones` + estado de carga y manejo de error de procesamiento (test happy path + error del backend)
- [x] 3.3 RED+GREEN: componente de preview de actividades y alumnos detectados (test: render del preview, no dispara cómputo)
- [x] 3.4 RED+GREEN: selección de actividades con marcar/desmarcar; confirmar deshabilitado sin selección (test: subconjunto + deshabilitado)
- [x] 3.5 RED+GREEN: formulario de umbral con Zod (default 60, rango 0–100); confirmar persiste umbral+actividades y recalcula (test: default, fuera de rango, confirmar)

## 4. Análisis académico (frontend-analisis-academico)

- [x] 4.1 RED+GREEN: hook + tabla de alumnos atrasados con estado vacío sin datos/actividades (test: tabla con datos + estado vacío)
- [x] 4.2 RED+GREEN: vista de ranking de actividades aprobadas, ordenada, sin alumnos con cero aprobadas (test de orden + filtro)
- [x] 4.3 RED+GREEN: vista de notas finales agrupadas por alumno (test de render)
- [x] 4.4 RED+GREEN: vista de reportes rápidos con métricas + estado informativo sin datos (test: métricas + estado informativo)

## 5. Entregas sin corregir (frontend-entregas-sin-corregir)

- [x] 5.1 RED+GREEN: upload del reporte de finalización (`multipart/form-data`) + estado de carga del cruce (test de subida)
- [x] 5.2 RED+GREEN: tabla de posibles entregas sin corregir (alumno/actividad) con estado vacío (test: con datos + vacío)
- [x] 5.3 RED+GREEN: acción de export del listado; deshabilitada sin datos (test: export habilitado/deshabilitado)

## 6. Comunicación a atrasados (frontend-comunicacion-atrasados)

- [x] 6.1 RED+GREEN: selección de destinatarios desde la vista de atrasados; acción deshabilitada sin selección (test)
- [x] 6.2 RED+GREEN: preview de asunto+cuerpo personalizado por alumno; no encola hasta confirmar (test de preview)
- [x] 6.3 RED+GREEN: `comunicacionApi` + hook de envío a la cola (C-12), mensajes en Pendiente tras confirmar (test de envío)
- [x] 6.4 RED+GREEN: hook de tracking con `refetchInterval` que corta en estados terminales; vista de transición Pendiente→En envío→OK/Fallido/Cancelado (test: avance de estado + corte del polling)

## 7. Monitor de seguimiento (frontend-monitor-seguimiento)

- [x] 7.1 RED+GREEN: hook + vista del monitor de alumnos asignados (alcance desde la sesión) con estado vacío (test: datos + vacío)
- [x] 7.2 RED+GREEN: filtros (alumno, correo, comisión, regional, actividad, mínimo cumplido) con esquema Zod; combinación de filtros (test de filtrado)
- [x] 7.3 RED+GREEN: acción de limpiar filtros que restablece la vista sin filtrar (test)

## 8. Cierre y verificación

- [x] 8.1 Verificar cobertura ≥80% líneas en los módulos nuevos
- [x] 8.2 Confirmar reglas duras: sin `any`, componentes PascalCase <200 LOC, todo fetch vía hooks de `services/`, sin acceso directo a la red en componentes
- [x] 8.3 Resolver o registrar como `TODO: (REVIEW)` cualquier discrepancia de contrato detectada en el paso 1.1
- [x] 8.4 Marcar `[x]` C-22 en `CHANGES.md`
