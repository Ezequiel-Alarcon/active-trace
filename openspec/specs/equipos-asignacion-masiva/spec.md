# equipos-asignacion-masiva Specification

## Purpose
TBD - created by archiving change equipos-docentes. Update Purpose after archive.
## Requirements
### Requirement: Asignación masiva de docentes a un equipo
El sistema SHALL permitir a un COORDINADOR o ADMIN crear múltiples asignaciones en una sola petición, especificando una lista de `usuario_id`, un `rol_id`, un `contexto_tipo` y `contexto_id`, y fechas de vigencia comunes, procesando cada asignación de forma independiente.

#### Scenario: Asignación masiva exitosa de 3 docentes
- **WHEN** un COORDINADOR envía `POST /api/equipos/asignacion-masiva` con 3 `usuario_id` válidos, `rol_id` de PROFESOR, `contexto_tipo == "Materia"`, `contexto_id` de una materia existente, `desde` y `hasta` futuros
- **THEN** el sistema crea 3 asignaciones, devuelve `creadas: [3 asignaciones]` y `fallidas: []`, y emite 3 eventos de auditoría `ASIGNACION_MODIFICAR`

#### Scenario: Asignación masiva con algunos fallos
- **WHEN** un COORDINADOR envía `POST /api/equipos/asignacion-masiva` con 3 `usuario_id`, donde uno no existe en el tenant
- **THEN** el sistema crea 2 asignaciones, devuelve `creadas: [2 asignaciones]` y `fallidas: [{usuario_id: <id>, motivo: "El usuario especificado no existe"}]`, con status 200 (parcial exitoso)

#### Scenario: Asignación masiva con rol inexistente
- **WHEN** un COORDINADOR envía `POST /api/equipos/asignacion-masiva` con un `rol_id` inexistente
- **THEN** el sistema devuelve `creadas: []` y `fallidas: [{motivo: "El rol especificado no existe"}]` para cada usuario del lote

#### Scenario: Asignación masiva con contexto inexistente
- **WHEN** un COORDINADOR envía `POST /api/equipos/asignacion-masiva` con `contexto_id` de una materia que no existe
- **THEN** el sistema devuelve `fallidas` para cada usuario del lote con motivo "El contexto Materia especificado no existe"

#### Scenario: Asignación masiva con fechas inválidas
- **WHEN** un COORDINADOR envía `POST /api/equipos/asignacion-masiva` con `hasta` anterior a `desde`
- **THEN** el sistema devuelve 422 Unprocessable Entity con detalle "hasta debe ser posterior a desde"

#### Scenario: Asignación masiva sin permisos
- **WHEN** un PROFESOR autenticado (sin permiso `equipos:asignar`) envía `POST /api/equipos/asignacion-masiva`
- **THEN** el sistema devuelve 403 Forbidden

### Requirement: Respuesta de asignación masiva detalla creadas y fallidas
El sistema SHALL devolver en la respuesta de asignación masiva dos listas: `creadas` con las asignaciones creadas exitosamente y `fallidas` con los errores por cada elemento del lote que no pudo crearse, incluyendo el `usuario_id` (cuando aplique) y el `motivo` del fallo.

#### Scenario: Respuesta de lote mixto
- **WHEN** se procesa un lote con 3 usuarios donde 2 se crean y 1 falla
- **THEN** la respuesta contiene `creadas: [AsignacionResponse, AsignacionResponse]` y `fallidas: [{usuario_id: <uuid>, motivo: "..."}]`

