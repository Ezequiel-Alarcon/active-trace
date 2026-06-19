# auditoria-log Specification

## ADDED Requirements

### Requirement: Log completo de auditoría con filtros
The system SHALL display the complete audit log with combined filters for date range, materia, usuario, and estado.

#### Scenario: Shows paginated audit log
- **WHEN** a user with `auditoria:ver` navigates to `/admin/auditoria/log`
- **THEN** the system calls `GET /api/audit/log?limit=50&offset=0`
- **AND** shows a DataTable with columns: fecha_hora, usuario, materia, accion, filas_afectadas, ip, user_agent
- **AND** shows pagination controls (next/prev, page indicator)

#### Scenario: FilterBar with combined filters
- **WHEN** the page loads
- **THEN** the FilterBar shows: rango fechas (date range picker), materia (select/search), usuario (select/search), estado (select)
- **WHEN** the user applies filters
- **THEN** the system calls `GET /api/audit/log?desde=<date>&hasta=<date>&materia_id=<id>&actor_id=<id>&limit=50&offset=0`

#### Scenario: Clear filters resets
- **WHEN** the user clicks "Limpiar filtros"
- **THEN** all filters reset and the log reloads unfiltered

#### Scenario: Pagination works with filters
- **WHEN** the user navigates to page 2 while filters are active
- **THEN** the system calls the same URL with offset=50 while preserving all filter params

#### Scenario: Empty log shows EmptyState
- **WHEN** no log entries match the filters
- **THEN** the system shows EmptyState with "No se encontraron registros de auditoría para los filtros seleccionados"

#### Scenario: Loading and error states
- **WHEN** fetching, shows loading indicator
- **WHEN** error, shows error message with retry action
