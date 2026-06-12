## ADDED Requirements

### Requirement: Approval guard for massive sends
The system SHALL require `comunicacion:aprobar` permission for messages sent to more than N recipients (configurable per tenant).

#### Scenario: User sends to small audience (within threshold)
- **WHEN** user enqueues messages to N or fewer recipients (tenant threshold)
- **THEN** messages enter directly in Pendiente state
- **AND** are eligible for immediate processing by the worker

#### Scenario: User sends to large audience (exceeds threshold)
- **WHEN** user enqueues messages to more than N recipients
- **THEN** messages enter in Pendiente state
- **AND** remain in Pendiente until approved by a user with comunicacion:aprobar
- **AND** a notification is sent to pending approvers

### Requirement: Approver can approve or reject a lote
A user with comunicacion:aprobar SHALL be able to approve or reject all messages in a lote.

#### Scenario: Approver approves a lote
- **WHEN** user with comunicacion:aprobar calls POST /api/comunicaciones/lotes/{lote_id}/aprobar
- **THEN** all messages in that lote transition from Pendiente to Enviando
- **AND** the worker picks them up for dispatch
- **AND** audit log records COMUNICACION_ENVIAR with approval context

#### Scenario: Approver rejects a lote
- **WHEN** user with comunicacion:aprobar calls POST /api/comunicaciones/lotes/{lote_id}/rechazar
- **THEN** all messages in that lote transition to Cancelado
- **AND** audit log records COMUNICACION_CANCELAR

### Requirement: Tenant can configure approval threshold
Each tenant SHALL be able to configure the recipient count threshold that triggers approval requirement.

#### Scenario: Tenant sets threshold to 5
- **WHEN** tenant admin configures umbral_aprobacion = 5
- **THEN** any send to more than 5 recipients requires approval
- **AND** sends to 5 or fewer proceed without approval