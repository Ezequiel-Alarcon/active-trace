## ADDED Requirements

### Requirement: Auditoría de carga de padrón

El sistema SHALL registrar un evento de auditoría `PADRON_CARGAR` cada vez que se importa una versión de padrón, incluyendo el `tenant_id`, el conteo de filas afectadas y los identificadores de materia/cohorte, sin filtrar PII.

#### Scenario: Importar emite PADRON_CARGAR

- **WHEN** se importa una versión de padrón con N entradas
- **THEN** se emite un evento `PADRON_CARGAR` con el `tenant_id` y `filas_afectadas = N`
- **AND** el evento no contiene emails ni otra PID en texto plano

### Requirement: Auditoría de vaciado de padrón

El sistema SHALL registrar un evento de auditoría `PADRON_VACIAR` (código distinto de `PADRON_CARGAR`) cada vez que se vacía un padrón, incluyendo el `tenant_id` y el conteo de versiones afectadas.

#### Scenario: Vaciar emite PADRON_VACIAR y no PADRON_CARGAR

- **WHEN** se vacía un padrón
- **THEN** se emite un evento `PADRON_VACIAR`
- **AND** no se emite `PADRON_CARGAR` por la operación de vaciado

#### Scenario: El código PADRON_VACIAR está en el vocabulario cerrado

- **WHEN** se emite `PADRON_VACIAR`
- **THEN** el código pertenece al conjunto cerrado de `ACTION_CODES` y no genera advertencia de código desconocido
