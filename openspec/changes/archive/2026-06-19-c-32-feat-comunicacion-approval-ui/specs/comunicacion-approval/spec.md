# comunicacion-approval Specification

## Purpose
UI de revisión y aprobación/rechazo de lotes de comunicaciones pendientes (F3.3). Permite a COORDINADOR/ADMIN ver lotes Pendiente, inspeccionar contenido, y aprobar o rechazar cada lote.

## ADDED Requirements

### Requirement: Listado de lotes pendientes

El sistema SHALL display a table of all lotes in estado Pendiente for the current tenant. The table SHALL include columns: fecha de creación (created_at), cantidad de destinatarios (total), asunto (truncated to 50 chars), y estado (siempre "Pendiente"). The table SHALL be sorted by created_at descending (most recent first).

#### Scenario: COORDINADOR accede a la página de aprobaciones
- **WHEN** a COORDINADOR navigates to `/comision/aprobaciones`
- **THEN** the system displays the table of pending lotes filtered by tenant

#### Scenario: ADMIN without comunicacion:aprobar permission is denied
- **WHEN** an ADMIN without `comunicacion:aprobar` permission navigates to `/comision/aprobaciones`
- **THEN** the system returns 403 Forbidden

#### Scenario: Table shows empty state when no pending lotes
- **WHEN** there are no pending lotes for the tenant
- **THEN** the system displays an EmptyState with message "No hay comunicaciones pendientes de aprobación"

### Requirement: Ver detalle de lote antes de aprobar/rechazar

Before approving or rejecting a lote, the user SHALL see a modal with the full lote details: asunto completo, cuerpo completo, lista de destinatarios (up to 20, with "... y N más" if overflow), nombre del docente que solicitó, y fecha de creación. The modal SHALL have "Aprobar" and "Rechazar" buttons and a "Cerrar" button.

#### Scenario: Click Ver opens detail modal
- **WHEN** user clicks "Ver" on a lote row
- **THEN** the system opens the DetalleLoteModal with that lote's data

#### Scenario: Modal shows truncated preview of long cuerpo
- **WHEN** the lote cuerpo exceeds 500 characters
- **THEN** the modal shows the first 500 chars followed by "..."

### Requirement: Aprobar lote de comunicaciones

The system SHALL allow a user with `comunicacion:aprobar` permission to approve a pending lote via `POST /api/comunicaciones/lotes/{lote_id}/aprobar`. On success, the lote transitions from Pendiente to Enviando (worker picks it up). The UI SHALL show a success toast and refresh the list.

#### Scenario: COORDINADOR approves a lote successfully
- **WHEN** a COORDINADOR clicks "Aprobar" in the modal for lote L
- **THEN** the system calls `POST /api/comunicaciones/lotes/L/aprobar`
- **AND** shows toast "Lote aprobado correctamente"
- **AND** closes the modal
- **AND** refreshes the pending lotes list

#### Scenario: Approve fails with server error
- **WHEN** a COORDINADOR clicks "Aprobar" and the server returns 500
- **THEN** the system shows an error toast "Error al aprobar el lote"
- **AND** the modal remains open

### Requirement: Rechazar lote de comunicaciones

The system SHALL allow a user with `comunicacion:aprobar` permission to reject a pending lote via `POST /api/comunicaciones/lotes/{lote_id}/rechazar`. On success, the lote transitions to Cancelado. The UI SHALL show a success toast and refresh the list.

#### Scenario: COORDINADOR rejects a lote
- **WHEN** a COORDINADOR clicks "Rechazar" in the modal for lote L
- **THEN** the system calls `POST /api/comunicaciones/lotes/L/rechazar`
- **AND** shows toast "Lote rechazado"
- **AND** closes the modal
- **AND** refreshes the pending lotes list

#### Scenario: PROFESOR without approve permission cannot reject
- **WHEN** a PROFESOR (without `comunicacion:aprobar`) tries to call the reject endpoint directly
- **THEN** the system returns 403 Forbidden

### Requirement: Confirmación antes de aprobar/rechazar

The system SHALL show a confirmation dialog before executing the approve or reject action, requiring the user to explicitly confirm or cancel.

#### Scenario: Confirm dialog on approve
- **WHEN** user clicks "Aprobar" in the modal
- **THEN** a confirmation dialog appears: "¿Aprobar este envío? Se procederá a enviar N mensajes."
- **AND** clicking "Confirmar" executes the approve
- **AND** clicking "Cancelar" closes the dialog without action

#### Scenario: Confirm dialog on reject
- **WHEN** user clicks "Rechazar" in the modal
- **THEN** a confirmation dialog appears: "¿Rechazar este envío? Esta acción cancelará N mensajes."
- **AND** clicking "Confirmar" executes the reject
- **AND** clicking "Cancelar" closes the dialog without action