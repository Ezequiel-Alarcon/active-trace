## ADDED Requirements

### Requirement: Sistema SHALL cerrar liquidacion de cohorte y periodo de forma inmutable
El sistema SHALL permitir a FINANZAS cerrar explicitamente todas las filas abiertas de liquidacion para una cohorte y periodo. Una vez cerradas, las filas SHALL quedar inmutables para updates de negocio y recalculos.

#### Scenario: Cierre exitoso inmutabiliza periodo
- **WHEN** FINANZAS confirma el cierre de liquidacion para cohorte `A` y periodo `2026-06`
- **THEN** el sistema cambia las filas abiertas de esa unidad a estado `Cerrada`
- **AND** rechaza cambios posteriores sobre esas filas

#### Scenario: Cierre sin confirmacion explicita falla
- **WHEN** FINANZAS solicita cerrar una liquidacion sin enviar confirmacion explicita
- **THEN** el sistema retorna `422 Unprocessable Entity`
- **AND** las filas permanecen en estado `Abierta`

### Requirement: Sistema SHALL auditar cierre de liquidacion
El sistema SHALL registrar una accion de auditoria `LIQUIDACION_CERRAR` cuando se cierre una liquidacion, incluyendo actor real, tenant, cohorte, periodo y cantidad de filas afectadas sin registrar PII sensible.

#### Scenario: Auditoria de cierre queda registrada
- **WHEN** FINANZAS cierra la liquidacion de `2026-06`
- **THEN** existe un registro append-only de auditoria con accion `LIQUIDACION_CERRAR`
- **AND** el detalle permite reconstruir cohorte, periodo y filas afectadas

### Requirement: Sistema SHALL exponer historial de liquidaciones cerradas
El sistema SHALL permitir consultar liquidaciones cerradas por periodo, cohorte y docente, respetando tenant y permisos.

#### Scenario: Consultar historial por docente
- **WHEN** FINANZAS consulta `GET /api/liquidaciones/historial?usuario_id=<id>`
- **THEN** el sistema retorna liquidaciones cerradas de ese docente en el tenant actual
- **AND** no retorna liquidaciones abiertas ni de otros tenants

### Requirement: Sistema SHALL exportar vista previa o liquidacion cerrada
El sistema SHALL permitir exportar una liquidacion abierta o cerrada para uso externo, preservando la misma segmentacion y totales que la vista consultada por API.

#### Scenario: Exportar vista previa sin cerrar
- **WHEN** FINANZAS exporta una liquidacion en estado `Abierta`
- **THEN** el sistema entrega un archivo o payload exportable
- **AND** la liquidacion permanece en estado `Abierta`
