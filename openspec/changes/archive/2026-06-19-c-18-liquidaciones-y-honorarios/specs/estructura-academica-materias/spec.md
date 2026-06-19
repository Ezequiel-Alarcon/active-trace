## ADDED Requirements

### Requirement: Materia SHALL support optional fixed Plus category mapping
El sistema SHALL permitir que una materia tenga una clave de Plus opcional perteneciente al catalogo fijo del programa/sistema. Una materia sin clave Plus SHALL ser valida y no SHALL generar adicional en liquidaciones.

#### Scenario: Crear materia sin clave Plus
- **WHEN** ADMIN crea una materia sin informar clave Plus
- **THEN** el sistema crea la materia exitosamente
- **AND** la materia no genera Plus en liquidaciones

#### Scenario: Actualizar materia con clave Plus existente
- **WHEN** ADMIN actualiza una materia con `plus_grupo=PROG` y `PROG` existe en el catalogo fijo
- **THEN** el sistema persiste el mapeo
- **AND** futuras liquidaciones pueden usar esa clave para calcular Plus

#### Scenario: Rechazar clave Plus inexistente
- **WHEN** ADMIN intenta asignar `plus_grupo=CUSTOM_TENANT` a una materia
- **THEN** el sistema retorna `422 Unprocessable Entity` o `409 Conflict`
- **AND** no crea una clave nueva por tenant
