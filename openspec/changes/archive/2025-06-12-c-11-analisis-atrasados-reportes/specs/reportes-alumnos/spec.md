# Reportes-Alumnos Spec

## ADDED Requirements

### Requirement: Endpoint GET /api/reportes/materia/{materia_id}

El sistema SHALL expose un endpoint `GET /api/reportes/materia/{materia_id}` que retorna un reporte completo de una materia.

El reporte incluye:
- `materia_id`, `materia_nombre`
- `cohorte_id`, `cohorte_nombre`
- `total_alumnos` (int)
- `alumnos`: array con:
  - `usuario_id`, `nombre`, `email`
  - `actividades`: array de:
    - `asignacion_id`, `asignacion_nombre`
    - `estado`: `"aprobado"` | `"atrasado"` | `"sin_nota"`
    - `nota`: valor actual o `null`
    - `umbral_pct`: umbral aplicado

#### Scenario: Reporte de materia con alumnos
- **WHEN** `GET /api/reportes/materia/{materia_id}` es llamado
- **THEN** retorna todas las actividades esperadas para cada alumno con su estado

### Requirement: Endpoint GET /api/reportes/notas-finales

El sistema SHALL expose un endpoint `GET /api/reportes/notas-finales` con notas finales agrupadas por materia.

Parámetros:
- `cohorte_id` (UUID, opcional): filtrar por cohorte
- `limit` (int, default 50, max 200)
- `offset` (int, default 0)

El response incluye:
- `materia_id`, `materia_nombre`
- `total_alumnos` (int)
- `aprobados` (int): cantidad con todas las actividades aprobadas
- `tasa_aprobacion` (float): `aprobados / total_alumnos * 100`
- `nota_promedio_global` (float | null): promedio de promedios

#### Scenario: Notas finales con cohorte
- **WHEN** `GET /api/reportes/notas-finales?cohorte_id=<uuid>` es llamado
- **THEN** solo incluye alumnos de esa cohorte

### Requirement: Endpoint GET /api/monitores/general

El sistema SHALL expose un endpoint `GET /api/monitores/general` que funciona como monitor para el rol PROFESOR.

El scope es: materias asignadas al profesor + sus alumnos.

Parámetros:
- `limit` (int, default 50, max 200)
- `offset` (int, default 0)

Response:
- `profesor_id`
- `materias`: array de:
  - `materia_id`, `materia_nombre`
  - `cantidad_alumnos`
  - `cantidad_atrasados`
  - `tasa_aprobacion_pct`

#### Scenario: Profesor consulta su monitor
- **WHEN** PROFESOR llama `GET /api/monitores/general`
- **THEN** retorna resumen de sus materias y alumnos

### Requirement: Endpoint GET /api/monitores/seguimiento

El sistema SHALL expose un endpoint `GET /api/monitores/seguimiento` que funciona como monitor para el rol TUTOR.

El scope es: solo sus tutorados.

Parámetros:
- `limit` (int, default 50, max 200)
- `offset` (int, default 0)

Response: mismo formato que `/monitores/general` pero scoped a tutorados.

#### Scenario: Tutor consulta sus tutorados
- **WHEN** TUTOR llama `GET /api/monitores/seguimiento`
- **THEN** retorna resumen de sus tutorados

### Requirement: Endpoint GET /api/monitores/coordinacion

El sistema SHALL expose un endpoint `GET /api/monitores/coordinacion` que funciona como monitor para COORDINADOR y ADMIN.

El scope es: todo el tenant con filtro de fechas obligatorio.

Parámetros:
- `desde` (date, requerido): fecha inicio de creación
- `hasta` (date, requerido): fecha fin de creación
- `limit` (int, default 50, max 200)
- `offset` (int, default 0)

**Validaciones**:
- Rango máximo: 365 días
- `desde` debe ser anterior a `hasta`

Response: resumen global del tenant en el rango de fechas.

#### Scenario: Admin consulta con rango válido
- **WHEN** ADMIN llama `GET /api/monitores/coordinacion?desde=2026-01-01&hasta=2026-06-01`
- **THEN** retorna resumen del tenant en ese período

#### Scenario: Admin consulta con rango > 365 días
- **WHEN** ADMIN llama `GET /api/monitores/coordinacion?desde=2025-01-01&hasta=2026-06-01`
- **THEN** retorna 400 Bad Request con mensaje de error

### Requirement: Permisos para reportes

Los endpoints de reportes requieren:
- `reportes:ver`: `/reportes/materia/{id}`, `/reportes/notas-finales`, `/monitores/general`, `/monitores/seguimiento`
- `reportes:ver`: `/monitores/coordinacion` (COORDINADOR, ADMIN)
- `reportes:exportar`: para endpoints de exportación

#### Scenario: Usuario sin permiso accede a reportes
- **WHEN** usuario sin `reportes:ver` llama `GET /api/reportes/materia/{id}`
- **THEN** el sistema retorna 403 Forbidden