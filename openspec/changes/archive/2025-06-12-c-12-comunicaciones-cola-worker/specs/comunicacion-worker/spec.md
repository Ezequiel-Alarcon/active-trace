## ADDED Requirements

### Requirement: Worker consume messages from cola Pendiente
The system SHALL have an async worker process that polls the database for messages in Pendiente state and transitions them to Enviando.

#### Scenario: Worker picks up a Pendiente message
- **WHEN** a message exists with estado = Pendiente and no lock held
- **THEN** the worker acquires a lock via SELECT FOR UPDATE SKIP LOCKED
- **AND** transitions the message to Enviando
- **AND** invokes the dispatch service
- **AND** on success transitions to Enviado with timestamp
- **AND** on failure transitions to Error with error detail

#### Scenario: Worker finds no messages
- **WHEN** no messages exist with estado = Pendiente
- **THEN** the worker sleeps for a configurable interval (default 5 seconds)
- **AND** retries

#### Scenario: Worker crash during Enviando leaves message stuck
- **WHEN** a message has been in Enviando for more than 5 minutes
- **THEN** a recovery job SHALL reset it to Pendiente
- **AND** the message becomes eligible for reprocessing

### Requirement: Dispatch integration with N8N/external service
The worker SHALL call an external dispatch service (N8N webhook or similar) to send the actual email.

#### Scenario: Dispatch returns success
- **WHEN** the dispatch service returns success (2xx)
- **THEN** the worker marks the message as Enviado
- **AND** records enviado_at timestamp

#### Scenario: Dispatch returns transient error
- **WHEN** the dispatch service returns 429 or 5xx
- **THEN** the worker marks the message as Error with detail
- **AND** logs the failure for monitoring

#### Scenario: Dispatch returns permanent failure
- **WHEN** the dispatch service returns 4xx (non-retryable)
- **THEN** the worker marks the message as Error immediately
- **AND** does not retry

### Requirement: Retry with exponential backoff
The worker SHALL retry transient failures with exponential backoff.

#### Scenario: Transient failure triggers retry
- **WHEN** a dispatch fails with transient error
- **THEN** the worker schedules a retry
- **AND** waits 2^attempt seconds before next try
- **AND** max 3 retries before marking Error