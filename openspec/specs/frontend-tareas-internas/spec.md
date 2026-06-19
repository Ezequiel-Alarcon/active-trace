# frontend-tareas-internas Specification

## Purpose
TBD - created by archiving change c-23-frontend-coordinacion. Update Purpose after archive.

## Requirements

### Requirement: Vista global de tareas (coordinación)

El sistema SHALL proveer una página con DataTable de todas las tareas del tenant, filtrable por docente asignado, asignador, materia, estado y búsqueda libre. Las tareas muestran: título, descripción, materia asociada, docente asignado, docente asignador, estado, fecha de creación, último comentario. Consume GET /api/tareas (C-16).

#### Scenario: Vista global con filtros

- **WHEN** un COORDINADOR navega a /coordinacion/tareas
- **THEN** el sistema SHALL mostrar una DataTable con todas las tareas del tenant
- **AND** SHALL mostrar FilterBar con filtros por estado, materia, docente

#### Scenario: Tabla vacía

- **WHEN** no hay tareas registradas
- **THEN** el sistema SHALL mostrar EmptyState "No hay tareas registradas"

### Requirement: Cambio de estado de tarea

El sistema SHALL proveer acciones en cada fila para cambiar el estado de la tarea: Pendiente → En progreso → Resuelta, o Cancelada desde cualquier estado no terminal. Consume PATCH /api/tareas/:id/estado (C-16).

#### Scenario: Cambio a "En progreso"

- **WHEN** el COORDINADOR cambia una tarea de "Pendiente" a "En progreso"
- **THEN** el StatusBadge de la tarea SHALL actualizarse al nuevo estado
- **AND** la tarea SHALL persistir con el nuevo estado

### Requirement: Comentarios en hilo de tarea

El sistema SHALL proveer una vista de detalle de tarea con el hilo de comentarios (autor + timestamp + texto). El COORDINADOR puede agregar nuevos comentarios. Consume GET /api/tareas/:id/comentarios y POST /api/tareas/:id/comentarios (C-16).

#### Scenario: Agregar comentario a tarea

- **WHEN** el COORDINADOR abre el detalle de una tarea
- **AND** escribe un comentario y hace clic en "Agregar"
- **THEN** el comentario SHALL aparecer en el hilo con autor y timestamp

### Requirement: Delegación de tarea

El sistema SHALL proveer la acción de delegar una tarea a otro docente. Consume POST /api/tareas/:id/delegar (C-16).

#### Scenario: Delegación exitosa

- **WHEN** el COORDINADOR selecciona un docente destino y confirma la delegación
- **THEN** el asignado de la tarea SHALL actualizarse
- **AND** el sistema SHALL mostrar un mensaje de confirmación
