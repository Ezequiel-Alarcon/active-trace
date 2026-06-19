# frontend-monitores-transversales Specification

## ADDED Requirements

### Requirement: Monitor general de actividades (F2.7)

El sistema SHALL proveer una página con vista transversal de todos los alumnos del tenant y su estado de actividades, con filtros por materia, regional, comisión, búsqueda libre por alumno, estado de actividad y criterio de clasificación. Acciones: aplicar filtros, exportar, limpiar selección. Consume GET /api/monitores/general (C-11).

#### Scenario: Monitor general muestra todos los alumnos

- **WHEN** un COORDINADOR navega a /coordinacion/monitor
- **THEN** el sistema SHALL mostrar DataTable con todos los alumnos del tenant
- **AND** SHALL mostrar FilterBar con filtros disponibles

#### Scenario: Filtro por materia

- **WHEN** el COORDINADOR selecciona una materia en el filtro
- **THEN** la tabla SHALL filtrarse a los alumnos de esa materia

#### Scenario: Exportar monitor

- **WHEN** el COORDINADOR hace clic en "Exportar"
- **THEN** el sistema SHALL descargar un archivo con los datos visibles

### Requirement: Monitor de seguimiento con rango de fechas (F2.9)

El sistema SHALL extender la vista de monitor de seguimiento existente (F2.8, features/monitor) con un filtro adicional de rango de fechas para acotar el período de análisis. Consume GET /api/monitores/seguimiento con parámetros fecha_desde/fecha_hasta (C-11).

#### Scenario: Filtro por rango de fechas

- **WHEN** un COORDINADOR establece un rango de fechas en el monitor de seguimiento
- **THEN** la tabla SHALL mostrar solo datos del período seleccionado

#### Scenario: Limpiar filtros

- **WHEN** el COORDINADOR hace clic en "Limpiar filtros"
- **THEN** todos los filtros SHALL restablecerse a valores por defecto
