# facturas-gestion Specification

## ADDED Requirements

### Requirement: Listado de facturas con filtros
The system SHALL display a list of invoice records from docentes que facturan, with filters for docente, estado, and date range.

#### Scenario: Shows filtered invoice list
- **WHEN** a user with `liquidaciones:ver` navigates to `/admin/liquidaciones/facturas`
- **THEN** the system shows a FilterBar with: docente (select/search), estado (select: Pendiente/Abonada/Todas), rango fechas (date range)
- **AND** calls `GET /api/facturas?docente_id=<id>&estado=<estado>&desde=<date>&hasta=<date>`
- **AND** shows a DataTable with columns: fecha_carga, docente, periodo, detalle, estado (StatusBadge: Pendiente/Abonada), acciones

#### Scenario: Empty list shows EmptyState
- **WHEN** no invoices match the filters
- **THEN** the system shows EmptyState with "No hay facturas para los filtros seleccionados"

#### Scenario: Clear filters resets to unfiltered list
- **WHEN** the user clicks "Limpiar filtros"
- **THEN** all filter fields reset to defaults and the list reloads unfiltered

### Requirement: Registrar factura pendiente
The system SHALL allow registering a new invoice as Pendiente.

#### Scenario: Register invoice form
- **WHEN** the user clicks "Registrar factura"
- **THEN** a modal form opens with fields: docente (select/search), periodo (month picker), detalle (textarea), archivo_adjunto (file upload, optional)
- **WHEN** submitted, the system calls `POST /api/facturas` with the form data as JSON (file URL if uploaded)
- **AND** on success, the modal closes, the table refreshes, and a success toast shows

### Requirement: Marcar factura como abonada
The system SHALL allow changing an invoice's estado from Pendiente to Abonada.

#### Scenario: Mark as paid with confirmation
- **WHEN** the user clicks "Marcar abonada" on a Pendiente row
- **THEN** a confirmation dialog shows "¿Confirmar que la factura ha sido abonada?"
- **WHEN** confirmed, the system calls `PATCH /api/facturas/{id}` with `{"estado": "Abonada"}`
- **AND** on success, the row's StatusBadge updates to "Abonada" (green)

#### Scenario: Already abonada hides action button
- **WHEN** an invoice has estado "Abonada"
- **THEN** no "Marcar abonada" button is shown for that row
