## ADDED Requirements

### Requirement: Sistema SHALL administrar salario base por rol con vigencia temporal
El sistema SHALL permitir a FINANZAS crear, listar, actualizar y soft-delete registros `SalarioBase` tenant-scoped para los roles COORDINADOR, NEXO, PROFESOR y TUTOR. Cada registro SHALL tener `rol`, `monto`, `desde` y `hasta` nullable, y SHALL rechazar solapamientos de vigencia para el mismo `(tenant_id, rol)`.

#### Scenario: Crear salario base vigente
- **WHEN** un usuario con permiso `liquidaciones:configurar-salarios` crea `SalarioBase` para `PROFESOR` con `monto=100000`, `desde=2026-06-01` y `hasta=NULL`
- **THEN** el sistema retorna `201 Created` con el registro tenant-scoped
- **AND** el registro queda disponible para calculos cuyo periodo este dentro de la vigencia

#### Scenario: Rechazar salario base solapado
- **WHEN** existe un `SalarioBase` para `PROFESOR` vigente desde `2026-06-01` sin fecha hasta
- **AND** FINANZAS intenta crear otro `SalarioBase` para `PROFESOR` con `desde=2026-07-01` y `hasta=NULL`
- **THEN** el sistema retorna `409 Conflict`

### Requirement: Sistema SHALL administrar plus por categoria fija y rol con vigencia temporal
El sistema SHALL permitir a FINANZAS crear, listar, actualizar y soft-delete registros `SalarioPlus` tenant-scoped para una clave de Plus existente del catalogo fijo y un rol docente. Cada registro SHALL tener `grupo`, `rol`, `descripcion`, `monto`, `desde` y `hasta` nullable, y SHALL rechazar claves que no existan en el catalogo fijo.

#### Scenario: Crear plus para clave fija existente
- **WHEN** existe la clave fija de Plus `PROG`
- **AND** FINANZAS crea `SalarioPlus` para `grupo=PROG`, `rol=PROFESOR`, `monto=25000`, `desde=2026-06-01`
- **THEN** el sistema retorna `201 Created`
- **AND** el plus puede aplicarse al calculo de docentes PROFESOR con comisiones activas de materias mapeadas a `PROG`

#### Scenario: Rechazar plus con clave no catalogada
- **WHEN** FINANZAS intenta crear `SalarioPlus` con `grupo=CUSTOM_TENANT`
- **THEN** el sistema retorna `422 Unprocessable Entity` o `409 Conflict`
- **AND** no crea una nueva clave de Plus por tenant

### Requirement: Sistema SHALL seleccionar salario vigente por periodo
El sistema SHALL seleccionar el salario base y plus cuyo rango de vigencia contenga el periodo liquidado, usando el mes del periodo `AAAA-MM` como fecha de referencia documentada por el service.

#### Scenario: Seleccionar base vigente para periodo
- **WHEN** existen bases para `TUTOR`: una vigente hasta `2026-05-31` y otra desde `2026-06-01`
- **AND** se calcula el periodo `2026-06`
- **THEN** el sistema usa la base con `desde=2026-06-01`

#### Scenario: Sin salario vigente impide calculo
- **WHEN** no existe `SalarioBase` vigente para el rol `NEXO` en `2026-06`
- **AND** se intenta calcular una liquidacion que requiere ese rol
- **THEN** el sistema rechaza el calculo con error de configuracion salarial incompleta
