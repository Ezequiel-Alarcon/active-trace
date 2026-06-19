# liquidaciones-periodo Specification

## ADDED Requirements

### Requirement: Vista de liquidaciones del período activo
The system SHALL display a view of the current period's salary liquidation for all docentes, segmented into three groups (General, NEXO, Factura) with header KPIs.

#### Scenario: Shows three segments with totals
- **WHEN** a user with `liquidaciones:ver` navigates to `/admin/liquidaciones`
- **THEN** the system shows three card sections: General (PROFESOR/TUTOR/COORDINADOR no factura), NEXO, and Docentes que facturan (informative)
- **AND** each section shows a DataTable with columns: docente, rol, comisiones, salario_base, plus, total
- **AND** header shows two KpiCards: "Total sin factura" and "Universo facturante"

#### Scenario: Filters by cohorte, mes, optional docente
- **WHEN** the user selects a cohorte and mes from FilterBar dropdowns
- **THEN** the system fetches `GET /api/liquidaciones?cohorte_id=<id>&mes=<YYYY-MM>&docente_id=<optional>`
- **AND** re-renders the three segments with filtered data
- **AND** empty segments show EmptyState

#### Scenario: Loading state shows skeleton
- **WHEN** the fetch is in progress
- **THEN** the system shows a loading indicator (skeleton/spinner) for table areas

#### Scenario: Error state shows message
- **WHEN** the API returns an error
- **THEN** the system shows an error message with retry action

### Requirement: Export liquidation data
The system SHALL allow exporting the current liquidation view.

#### Scenario: Export button triggers download
- **WHEN** the user clicks "Exportar"
- **THEN** the system calls `GET /api/liquidaciones/export?cohorte_id=<id>&mes=<YYYY-MM>`
- **AND** triggers a file download (CSV/XLSX)
- **AND** shows a success toast on completion
