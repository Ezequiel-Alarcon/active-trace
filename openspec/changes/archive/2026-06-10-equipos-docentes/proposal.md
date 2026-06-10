## Why

C-07 (usuarios-y-asignaciones) ya permite ABM individual de asignaciones, pero los coordinadores no pueden operar sobre equipos docentes completos. Necesitan asignar múltiples docentes a una materia×cohorte de una sola vez, clonar equipos entre períodos para el setup de cuatrimestre (FL-03), ajustar vigencias en bloque y exportar la composición del equipo. Sin esto, el flujo de coordinación es manual e inviable a escala.

## What Changes

- **Mis equipos del docente (F4.2)**: endpoint para que un PROFESOR/TUTOR/COORDINADOR consulte sus propias asignaciones con filtros por cohorte, materia y estado de vigencia
- **Gestión de asignaciones (F4.3)**: endpoints de consulta especializados sobre asignaciones (por materia×cohorte, con datos expandidos del usuario)
- **Asignación masiva (F4.4)**: endpoint batch que crea múltiples asignaciones (usuarios × rol × contexto) en una sola petición, con informe de creadas/fallidas
- **Clonar equipo entre períodos (F4.5, RN-12)**: endpoint que duplica asignaciones vigentes de una cohorte origen a una cohorte destino, ajustando fechas de vigencia
- **Modificar vigencia general del equipo (F4.6)**: endpoint batch que actualiza desde/hasta de todas las asignaciones filtradas por materia×cohorte (y opcionalmente rol)
- **Exportar equipo a archivo (F4.7)**: endpoint de descarga CSV con datos del equipo (nombre, apellido, email, rol, materia, cohorte, vigencia)
- **Audit**: toda operación batch emite eventos de auditoría con action code `ASIGNACION_MODIFICAR`

## Capabilities

### New Capabilities
- `equipos-mis-equipos`: consulta de asignaciones propias del docente autenticado, con filtros y datos expandidos
- `equipos-asignacion-masiva`: creación batch de múltiples asignaciones con validación parcial y reporte de fallidas
- `equipos-clonar`: duplicación de asignaciones vigentes entre cohortes con ajuste de fechas (RN-12)
- `equipos-vigencia`: modificación en bloque de fechas desde/hasta para asignaciones filtradas por materia×cohorte
- `equipos-export`: exportación CSV del equipo docente con datos descifrados del usuario

### Modified Capabilities
<!-- No existing specs to modify — all capabilities are new. -->

## Impact

- **Nuevo service**: `app/services/equipos.py` — `EquipoService` con operaciones batch sobre `Asignacion`
- **Nuevo router**: `app/routers/equipos.py` — `equipo_router` montado en `/api/equipos` con guard `equipos:asignar` (COORDINADOR, ADMIN)
- **Nuevos schemas**: `app/schemas/equipos.py` — schemas para request/response de cada endpoint
- **Nuevo action code**: `ASIGNACION_MODIFICAR` en `app/core/audit.py` para operaciones batch
- **Modifica**: `app/api/v1/main_router.py` — incluye `equipo_router`
- **Sin migración**: opera sobre tablas existentes de C-07
- **Sin nuevos modelos**: opera sobre `Asignacion`, `Usuario`, `Rol`, `Carrera`, `Cohorte`, `Materia` existentes
- **Dependencias**: C-07 (usuarios-y-asignaciones) — ya implementado
