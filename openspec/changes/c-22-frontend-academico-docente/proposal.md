## Why

El shell de frontend (C-21) ya entrega autenticación, guards por permiso y layout, pero el PROFESOR todavía no tiene ninguna pantalla para operar su comisión. El flujo de mayor valor del producto — importar calificaciones del LMS, detectar atrasados y comunicarles con aprobación (FL-02, FL-04) — vive hoy solo en el backend (C-09 a C-12). Esta feature expone ese flujo central a los roles docentes (PROFESOR, TUTOR), cerrando el camino crítico "importar → analizar → comunicar" en la SPA.

## What Changes

- Nueva sección de **gestión de comisión** para el PROFESOR: selección de materia/cohorte y navegación entre las vistas de análisis.
- **Importación de calificaciones** con preview de actividades y alumnos detectados, selección de actividades a incluir y configuración del umbral de aprobación (default 60%).
- **Vistas de análisis** computadas por el backend: alumnos atrasados, ranking de actividades aprobadas, notas finales agrupadas y reportes rápidos por materia (con estado vacío cuando no hay datos/actividades seleccionadas).
- **Detección de entregas sin corregir**: importación del reporte de finalización del LMS, tabla de posibles entregas sin corregir y export descargable.
- **Comunicación a alumnos atrasados**: selección de destinatarios, preview de asunto+cuerpo por alumno, envío a la cola y **tracking de estado en tiempo real** (Pendiente → En envío → OK / Fallido / Cancelado) vía polling.
- **Monitor de seguimiento** (vista tutor/profesor) del estado de actividades de los alumnos asignados, con filtros (alumno, correo, comisión, regional, actividad, mínimo cumplido).
- Registro de las nuevas rutas protegidas por permiso en el router existente y entradas de menú en `AppLayout`.

No hay cambios de contrato de backend: esta feature **consume** los endpoints ya construidos en C-10, C-11 y C-12.

## Capabilities

### New Capabilities
- `frontend-comision-workspace`: contenedor de gestión de comisión del PROFESOR — selección de materia/cohorte, navegación entre vistas de análisis y registro de rutas/menú protegidas por permiso.
- `frontend-calificaciones-import`: flujo de importación de calificaciones — upload del export del LMS, preview de actividades/alumnos, selección de actividades y configuración del umbral.
- `frontend-analisis-academico`: vistas de lectura de los cómputos del backend — atrasados, ranking, notas finales y reportes rápidos, con estados vacíos.
- `frontend-entregas-sin-corregir`: importación del reporte de finalización, tabla de entregas potencialmente sin corregir y export.
- `frontend-comunicacion-atrasados`: selección de atrasados, preview de comunicación, envío a la cola y tracking de estados en tiempo real.
- `frontend-monitor-seguimiento`: monitor filtrable del estado de actividades de los alumnos asignados al docente (vista tutor/profesor).

### Modified Capabilities
<!-- Ninguna: C-21 (frontend-app-shell, frontend-route-guard) provee el shell; esta feature solo agrega rutas/menú sin cambiar sus requisitos. -->

## Impact

- **Frontend** (`frontend/src/features/`): nuevos módulos feature-based (`comision`, `calificaciones`, `analisis`, `entregas`, `comunicacion`, `monitor`) cada uno con `components/`, `hooks/`, `services/`, `types/`, `pages/`.
- **Router/Layout** (`frontend/src/shared/`): nuevas rutas envueltas en `RequirePermission` y entradas de menú en `AppLayout` (reemplaza los `TODO: (FEAT) C-22` existentes en `router.tsx`).
- **Servicios HTTP**: nuevos clientes Axios sobre el `apiClient` centralizado (`@/shared/services/api`) que consumen endpoints de C-10/C-11/C-12.
- **Backend**: sin cambios. Solo consumo de API existente.
- **Permisos consumidos**: `calificaciones:importar`, `atrasados:ver`, `comunicacion:enviar`.
- **Dependencias externas**: ninguna nueva; stack ya instalado por C-21 (TanStack Query, RHF+Zod, Tailwind, Axios).
