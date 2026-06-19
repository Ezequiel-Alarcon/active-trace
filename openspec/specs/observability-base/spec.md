## ADDED Requirements

### Requirement: audit_emit() SHALL write to the AuditLog table via AuditLogRepository

The `audit_emit()` function in `app/core/audit.py` SHALL call `AuditLogRepository.create(session, ...)` to persist audit events to the `AuditLog` database table. The function SHALL accept an `AsyncSession` as a required parameter. Callers MUST pass an active DB session. If no session is available (e.g., background task context), the function MAY fall back to logging the event to the structured JSON logger.

#### Scenario: audit_emit persists an event to the AuditLog table

- **WHEN** `audit_emit(session, action="AUTH_LOGIN_OK", user_id=U1, tenant_id=T1)` is called
- **THEN** a new row is created in the `AuditLog` table
- **AND** the row contains `action = "AUTH_LOGIN_OK"`, `user_id = U1`, `tenant_id = T1`
- **AND** no audit event is lost on application restart

#### Scenario: All existing callers pass a DB session

- **WHEN** `audit_emit` is called from any router, service, or repository
- **THEN** an active `AsyncSession` is available and passed as the first argument
- **AND** the audit event is written to the database, not to a logger

### Requirement: Logging estructurado en JSON

El sistema SHALL emitir sus logs en formato estructurado JSON en una sola línea por evento, de modo que sean parseables por agregadores de logs. Cada registro SHALL incluir, como mínimo, timestamp, nivel y mensaje. Los logs NO SHALL contener secretos ni PII en texto plano.

#### Scenario: Formato de log parseable

- **WHEN** la aplicación emite un log durante su operación
- **THEN** la salida es una línea JSON válida con campos de timestamp, nivel y mensaje

### Requirement: Instrumentación OpenTelemetry inicial

El sistema SHALL instrumentar la aplicación FastAPI con OpenTelemetry para trazas, de forma que cada request HTTP genere un span asociado. La instrumentación SHALL ser configurable por entorno (p. ej. activable/desactivable y con destino de exportación parametrizable), sin acoplar el arranque a un backend de telemetría específico.

#### Scenario: Request genera un span

- **WHEN** llega una request HTTP a la aplicación con la instrumentación activada
- **THEN** se genera un span de OpenTelemetry que representa esa request

#### Scenario: Telemetría no bloquea el arranque

- **WHEN** la aplicación inicia sin un backend de exportación de telemetría configurado
- **THEN** la app arranca normalmente y sirve requests sin fallar por la ausencia del exporter
