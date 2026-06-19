# frontend-coloquios-admin Specification

## ADDED Requirements

### Requirement: Panel de métricas de coloquios

El sistema SHALL proveer un panel con KpiCards mostrando: total de alumnos cargados, instancias activas, reservas activas, notas registradas. Consume GET /api/coloquios/metricas (C-14).

#### Scenario: Panel muestra métricas

- **WHEN** un COORDINADOR navega a /coordinacion/coloquios
- **THEN** el sistema SHALL mostrar 4 KpiCards con las métricas principales

### Requirement: Creación de convocatoria de coloquio

El sistema SHALL proveer un formulario para crear una convocatoria: materia, instancia, días disponibles con cupos. Consume POST /api/coloquios/convocatorias (C-14).

#### Scenario: Creación exitosa

- **WHEN** el COORDINADOR completa el formulario de convocatoria
- **AND** hace clic en "Crear"
- **THEN** el sistema SHALL crear la convocatoria
- **AND** SHALL mostrar la nueva convocatoria en el listado

### Requirement: Listado de convocatorias

El sistema SHALL proveer una DataTable de todas las convocatorias con métricas: materia, instancia, días disponibles, convocados, reservas activas, cupos libres. Acciones: editar, cerrar. Consume GET /api/coloquios/convocatorias (C-14).

#### Scenario: Listado con métricas

- **WHEN** un COORDINADOR ve el listado de convocatorias
- **THEN** cada fila SHALL mostrar materia, instancia, cupos libres, reservas activas

### Requirement: Agenda de reservas activas

El sistema SHALL proveer una vista de todas las reservas activas por convocatoria, con datos del alumno, día y hora reservada. Consume GET /api/coloquios/reservas (C-14).

#### Scenario: Agenda de reservas

- **WHEN** el COORDINADOR abre una convocatoria
- **THEN** SHALL ver la agenda de reservas activas con alumno, día y hora
