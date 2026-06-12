## ADDED Requirements

### Requirement: Message state transitions are auditable
Every state transition of a Comunicacion SHALL be recorded in the audit log with code COMUNICACION_ENVIAR.

#### Scenario: Message transitions to Enviando
- **WHEN** a message transitions from Pendiente to Enviando
- **THEN** the system creates an audit log entry with accion = COMUNICACION_ENVIAR
- **AND** includes detalle with previous state, new state, and message_id

#### Scenario: Message transitions to Enviado
- **WHEN** a message transitions from Enviando to Enviado
- **THEN** the system creates an audit log entry with accion = COMUNICACION_ENVIAR
- **AND** includes detalle with dispatch timestamp and message_id

#### Scenario: Message transitions to Error
- **WHEN** a message transitions from Enviando to Error
- **THEN** the system creates an audit log entry with accion = COMUNICACION_ENVIAR
- **AND** includes detalle with error reason and message_id

#### Scenario: Message is cancelled
- **WHEN** a message transitions from any state to Cancelado
- **THEN** the system creates an audit log entry with accion = COMUNICACION_CANCELAR
- **AND** includes detalle with reason and message_id

### Requirement: States are mutually exclusive and exhaustive
A Comunicacion SHALL be in exactly one state at any time: Pendiente | Enviando | Enviado | Error | Cancelado.

#### Scenario: Invalid state transition is rejected
- **WHEN** code attempts to transition Enviado to Pendiente
- **THEN** the system raises an invalid state transition error
- **AND** does not update the record

### Requirement: Enviado state is terminal
Once a message reaches Enviado, it SHALL NOT transition to any other state.

#### Scenario: Attempt to transition Enviado
- **WHEN** code attempts to change state of an Enviado message
- **THEN** the operation is rejected with error "Enviado is a terminal state"