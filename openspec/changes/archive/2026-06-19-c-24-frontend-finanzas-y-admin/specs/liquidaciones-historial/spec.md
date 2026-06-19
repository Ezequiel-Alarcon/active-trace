# liquidaciones-historial Specification

## ADDED Requirements

### Requirement: Historial de liquidaciones cerradas
The system SHALL display a history of closed liquidations from previous periods for consultation and audit.

#### Scenario: Shows list of closed liquidations
- **WHEN** a user with `liquidaciones:ver` navigates to `/admin/liquidaciones/historial`
- **THEN** the system calls `GET /api/liquidaciones/historial`
- **AND** shows a DataTable with columns: período (mes/año), fecha_cierre, total_general, total_sin_factura, total_con_factura
- **AND** each row shows a StatusBadge "Cerrada"

#### Scenario: Empty history shows EmptyState
- **WHEN** no closed liquidations exist
- **THEN** the system shows EmptyState with message "No hay liquidaciones cerradas"

#### Scenario: Click row to view detail
- **WHEN** the user clicks a row in the historial DataTable
- **THEN** the system navigates to a read-only detail view of that liquidation
- **AND** shows the same three segments (General/NEXO/Factura) as the period view, but all fields are read-only
- **AND** no close/export buttons are available

#### Scenario: Loading and error states
- **WHEN** the fetch is in progress, the system shows loading indicator
- **WHEN** the API returns an error, the system shows error message with retry
