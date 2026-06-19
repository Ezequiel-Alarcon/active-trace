## ADDED Requirements

### Requirement: Usuario SHALL expose modalidad facturante for liquidation routing
El sistema SHALL persistir y exponer si un usuario docente trabaja bajo modalidad facturante. El valor por defecto para usuarios existentes y nuevos SHALL ser no facturante, salvo que ADMIN/FINANZAS lo configure explicitamente.

#### Scenario: Usuario nuevo queda no facturante por defecto
- **WHEN** ADMIN crea un usuario sin informar modalidad facturante
- **THEN** el sistema persiste al usuario como no facturante
- **AND** el usuario participa del flujo de liquidacion general Base + Plus si tiene asignaciones docentes aplicables

#### Scenario: Usuario facturante se enruta a facturas
- **WHEN** ADMIN o FINANZAS marca un docente como facturante
- **THEN** el calculo de liquidacion lo muestra con `excluido_por_factura=true`
- **AND** su pago operativo se gestiona desde el modulo de facturas

#### Scenario: Request con campo desconocido sigue rechazandose
- **WHEN** se actualiza la modalidad facturante con un payload que incluye un campo no declarado
- **THEN** el sistema retorna `422 Unprocessable Entity`
- **AND** no modifica el usuario
