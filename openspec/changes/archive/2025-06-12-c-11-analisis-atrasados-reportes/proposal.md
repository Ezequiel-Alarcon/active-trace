# C-11: Analisis de Atrasados y Reportes

## Why

Los actores del sistema (profesores, tutores, coordinadores) necesitan visibilidad sobre qué alumnos están atrasados en sus actividades para intervenir a tiempo. Actualmente no existe forma de consultar alumnos sin calificación o con calificación insuficiente contra el umbral, ni rankings de progreso. Este change implementa la lógica derivada de "atrasado", los rankings de actividades aprobadas, y los reportes necesarios para los 3 monitores del sistema.

## What Changes

- Definición formal de **alumno atrasado**: actividad existe en `VersionPadron` para la materia/cohorte del alumno, pero no tiene `Calificacion` O la calificación existe pero `derivar_aprobado()` retorna `False`
- Endpoint de **alumnos atrasados** con filtros por materia, cohorte, tutor
- **Ranking de actividades aprobadas** por alumno usando window function (cantidad de aprobadas desc, desempate por nota promedio)
- **Reportes por materia**: lista de alumnos, estado de cada actividad, nota actual, estado (aprobado/atrasado)
- **Notas finales agrupadas**: promedio por materia, cantidad de aprobados/totales
- **Exportar TPs sin corregir**: alumnos con actividad en VersionPadron que tiene `nota=null`
- **3 monitores** con scopes diferenciados:
  - Monitor general (profesor): sus alumnos, sus materias
  - Monitor de seguimiento (tutor): sus tutorados
  - Monitor de coordinación/admin: todos los alumnos del tenant con rango de fechas

## Capabilities

### New Capabilities
- `analisis-atrasados`: Lógica derivada para detectar alumnos atrasados (sin calificación o derivada=false) contra VersionPadron
- `reportes-alumnos`: Rankings, reportes por materia, notas finales agrupadas
- `exportacion-tps`: Extracción de TPs sin corregir para re-importación

### Modified Capabilities
- (ninguna — no cambia comportamiento de specs existentes)

## Impact

- **Nuevos modelos**: ninguno — la lógica es derivada sobre modelos existentes (C-09, C-10)
- **Nuevos endpoints**: 6+ endpoints en `/api/analisis/`, `/api/reportes/`, `/api/exportacion/`
- **Permisos**: `analisis:ver`, `reportes:ver`, `reportes:exportar` — roles: profesor, tutor, coordinator, admin
- **Dependencias**: C-09 (`VersionPadron`), C-10 (`Calificacion`, `UmbralMateria`, `derivar_aprobado`)
- **Sin cambios a modelos de datos**: no requiere migración