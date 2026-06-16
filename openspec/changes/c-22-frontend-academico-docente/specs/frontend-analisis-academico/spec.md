## ADDED Requirements

### Requirement: Vista de alumnos atrasados

El sistema SHALL mostrar la tabla de alumnos atrasados de la comisión seleccionada, computada por el backend (alumnos con actividades faltantes o nota inferior al umbral). La tabla MUST obtener sus datos vía un hook de TanStack Query sobre el endpoint de C-11 y MUST mostrar un estado vacío informativo cuando no hay datos importados o no se seleccionaron actividades.

#### Scenario: Tabla de atrasados con datos

- **WHEN** la comisión tiene calificaciones importadas y actividades seleccionadas con atrasados
- **THEN** se renderiza la tabla de atrasados con los alumnos devueltos por el backend

#### Scenario: Estado vacío sin datos o sin actividades

- **WHEN** la comisión no tiene datos importados o no tiene actividades seleccionadas
- **THEN** la vista muestra un estado vacío informativo en lugar de una tabla

### Requirement: Ranking de actividades aprobadas

El sistema SHALL mostrar el ranking de actividades aprobadas por alumno, ordenado por cantidad de actividades aprobadas según el cómputo del backend. La vista MUST incluir solo alumnos con al menos una actividad aprobada.

#### Scenario: Ranking ordenado

- **WHEN** el PROFESOR abre la vista de ranking de una comisión con datos
- **THEN** se renderiza la tabla ordenada de mayor a menor cantidad de actividades aprobadas
- **AND** no aparecen alumnos con cero actividades aprobadas

### Requirement: Notas finales agrupadas

El sistema SHALL mostrar las notas finales agrupadas por alumno calculadas por el backend a partir de las actividades configuradas, en una vista lista para revisión.

#### Scenario: Notas finales por alumno

- **WHEN** el PROFESOR abre la vista de notas finales de una comisión con actividades configuradas
- **THEN** se renderiza la nota final por alumno según el agrupamiento del backend

### Requirement: Reportes rápidos por materia

El sistema SHALL mostrar una vista de reportes rápidos con las métricas clave de la materia (actividades, aprobaciones, tendencias) provistas por el backend. La vista MUST mostrar un estado informativo cuando aún no hay datos o no se seleccionaron actividades.

#### Scenario: Reportes con métricas

- **WHEN** la comisión tiene datos importados y actividades seleccionadas
- **THEN** la vista de reportes rápidos muestra las métricas clave de la materia

#### Scenario: Reportes en estado informativo sin datos

- **WHEN** la comisión aún no tiene datos o actividades seleccionadas
- **THEN** la vista de reportes muestra un estado informativo en lugar de métricas
