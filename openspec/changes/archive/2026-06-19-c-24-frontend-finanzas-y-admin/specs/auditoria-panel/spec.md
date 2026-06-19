# auditoria-panel Specification

## ADDED Requirements

### Requirement: Panel de auditoría con KPIs y métricas
The system SHALL display an audit dashboard with KPIs of system activity, consuming C-19 backend endpoints.

#### Scenario: Shows actions per day chart
- **WHEN** a user with `auditoria:ver` navigates to `/admin/auditoria`
- **THEN** the system calls `GET /api/audit/metrics/actions-per-day`
- **AND** shows a simple bar/line visualization of action counts per day (last 30 days by default)

#### Scenario: Shows communication status by docente/materia
- **WHEN** the page loads
- **THEN** the system calls `GET /api/audit/metrics/comunicacion-status`
- **AND** shows a DataTable with columns: materia, docente, pendientes, enviando, ok, fallidos, cancelados
- **AND** each count uses StatusBadge with the corresponding estado color

#### Scenario: Shows interactions by docente/materia
- **WHEN** the page loads
- **THEN** the system calls `GET /api/audit/metrics/interactions`
- **AND** shows a DataTable with columns: materia, docente, tipo_accion, count

#### Scenario: Shows last actions log
- **WHEN** the page loads
- **THEN** the system calls `GET /api/audit/metrics/last-actions?limit=10`
- **AND** shows a compact DataTable with columns: fecha_hora, usuario, materia, accion, ip

### Requirement: FilterBar for audit panel
The system SHALL provide filters for the audit panel metrics.

#### Scenario: Filters scope the data
- **WHEN** the user applies filters (rango fechas, materia, usuario)
- **THEN** all KPI sections and tables re-fetch with the filter parameters
- **AND** the FilterBar provides a "Limpiar filtros" button

### Requirement: Loading and empty states
The system SHALL show appropriate states for each audit section.

#### Scenario: Loading state
- **WHEN** metrics are loading
- **THEN** each KpiCard/DataTable section shows a loading skeleton

#### Scenario: Empty state
- **WHEN** a metric section has no data
- **THEN** that section shows EmptyState with contextual message (e.g., "No hay acciones registradas en el período")
