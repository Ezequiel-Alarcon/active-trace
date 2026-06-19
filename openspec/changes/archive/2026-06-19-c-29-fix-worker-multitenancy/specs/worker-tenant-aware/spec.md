## ADDED Requirements

### Requirement: Worker receives tenant_id via configuration

The comunicacion worker MUST receive the `tenant_id` it should process via the `COMUNICACION_WORKER_TENANT_ID` environment variable or setting. The worker SHALL NOT process messages from any tenant other than the configured one.

#### Scenario: Worker starts with valid tenant_id

- **WHEN** the worker starts with `COMUNICACION_WORKER_TENANT_ID=T1`
- **THEN** all database queries executed by the worker include `tenant_id = T1` as a filter
- **AND** no message from any other tenant is ever selected

#### Scenario: Worker fails fast when tenant_id is not configured

- **WHEN** the worker starts without `COMUNICACION_WORKER_TENANT_ID` set
- **THEN** the worker raises a configuration error and exits immediately
- **AND** no messages are processed

### Requirement: All worker queries are tenant-scoped

Every SQL query executed by the comunicacion worker MUST include `tenant_id` as a filter condition. This applies to `_recovery_job`, `run_poll_loop`, and any other query against the `comunicacion` table.

#### Scenario: _recovery_job filters by tenant_id

- **WHEN** `_recovery_job` is called with `tenant_id = T1`
- **THEN** the SELECT statement includes `WHERE tenant_id = T1`
- **AND** only stuck messages belonging to tenant T1 are recovered

#### Scenario: run_poll_loop filters by tenant_id

- **WHEN** `run_poll_loop` processes messages with `tenant_id = T1`
- **THEN** the poll SELECT includes `WHERE tenant_id = T1`
- **AND** only Pendiente messages belonging to tenant T1 are selected

#### Scenario: Worker does not process cross-tenant messages

- **WHEN** tenant T1 has 5 Pendiente messages and tenant T2 has 10 Pendiente messages
- **AND** the worker is configured for tenant T1
- **THEN** only the 5 messages from T1 are processed
- **AND** the 10 messages from T2 are never touched by this worker instance
