# frontend-encuentros-admin Specification

## Purpose
TBD - created by archiving change c-23-frontend-coordinacion. Update Purpose after archive.

## Requirements

### Requirement: Vista transversal de encuentros (coordinación/admin)

El sistema SHALL proveer una página con DataTable de todos los encuentros del tenant, mostrando materia, docente, día, horario, enlace, estado, grabación. Filtros por materia, docente, estado, rango de fechas. Consume GET /api/encuentros (C-13).

#### Scenario: Vista de todos los encuentros

- **WHEN** un COORDINADOR navega a /coordinacion/encuentros
- **THEN** el sistema SHALL mostrar DataTable con todos los encuentros del tenant

#### Scenario: Filtro por docente

- **WHEN** el COORDINADOR filtra por nombre de docente
- **THEN** la tabla SHALL mostrar solo encuentros de ese docente

### Requirement: Administración de slots recurrentes

El sistema SHALL proveer una vista de slots de encuentro recurrente (materia, día, horario, fecha inicio, cantidad semanas, título, enlace). Consume la API de slots de C-13.

#### Scenario: Listado de slots

- **WHEN** un COORDINADOR navega a la sección de slots
- **THEN** el sistema SHALL mostrar los slots recurrentes configurados por materia

### Requirement: Registro y exportación de guardias

El sistema SHALL proveer una página de guardias (tutor que cubrió, materia, día, horario, estado, comentarios) con exportación. Consume GET /api/guardias y GET /api/guardias/exportar (C-13).

#### Scenario: Filtro de guardias por rango de fechas

- **WHEN** el COORDINADOR filtra guardias por rango de fechas
- **THEN** la tabla SHALL mostrar solo las guardias en ese rango

#### Scenario: Exportar guardias

- **WHEN** el COORDINADOR hace clic en "Exportar"
- **THEN** el sistema SHALL descargar un archivo con el registro de guardias
