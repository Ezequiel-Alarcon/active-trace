## ADDED Requirements

### Requirement: Preview renders message before sending
The system SHALL provide a preview endpoint that renders the message (asunto + cuerpo) without persisting or enqueueing.

#### Scenario: User requests preview
- **WHEN** user calls POST /api/comunicaciones/preview with asunto and cuerpo
- **THEN** the system returns a rendered preview with the same subject and body
- **AND** does not create any Comunicacion record

#### Scenario: Preview requires comunicacion:enviar permission
- **WHEN** user without comunicacion:enviar permission calls preview endpoint
- **THEN** the system returns 403 Forbidden

### Requirement: Preview includes recipient address
The preview SHALL include the destination email address for context.

#### Scenario: Preview shows recipient
- **WHEN** user requests preview with destinatario email
- **THEN** the preview response includes the destinatario address
- **AND** shows how the message will appear to that recipient