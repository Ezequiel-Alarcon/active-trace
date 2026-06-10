# equipos-mis-equipos Specification

## Purpose
TBD - created by archiving change equipos-docentes. Update Purpose after archive.
## Requirements
### Requirement: Docente consulta sus propias asignaciones
El sistema SHALL permitir a un usuario autenticado con rol PROFESOR, TUTOR o COORDINADOR consultar la lista de sus asignaciones vigentes, incluyendo datos expandidos del contexto (nombre de materia, carrera, cohorte) y del rol asignado.

#### Scenario: Docente consulta sus equipos sin filtros
- **WHEN** un PROFESOR autenticado solicita `GET /api/equipos/mis-equipos`
- **THEN** el sistema devuelve todas las asignaciones donde `usuario_id` coincide con el `user_id` del JWT, con datos expandidos (nombre de usuario, rol, contexto, vigencia)

#### Scenario: Docente filtra por cohorte
- **WHEN** un PROFESOR autenticado solicita `GET /api/equipos/mis-equipos?cohorte_id=<uuid>`
- **THEN** el sistema devuelve solo las asignaciones del usuario cuyo `contexto_tipo == "Cohorte"` y `contexto_id == cohorte_id`, o cuyo contexto (Materia) pertenezca a esa cohorte

#### Scenario: Docente filtra por estado de vigencia
- **WHEN** un PROFESOR autenticado solicita `GET /api/equipos/mis-equipos?estado_vigencia=Vigente`
- **THEN** el sistema devuelve solo las asignaciones cuya propiedad `estado_vigencia` sea "Vigente"

#### Scenario: Usuario sin asignaciones
- **WHEN** un usuario autenticado sin asignaciones solicita `GET /api/equipos/mis-equipos`
- **THEN** el sistema devuelve una lista vacía con status 200

#### Scenario: Usuario no autenticado
- **WHEN** una petición sin token JWT solicita `GET /api/equipos/mis-equipos`
- **THEN** el sistema devuelve 401 Unauthorized

### Requirement: Respuesta de mis-equipos incluye datos expandidos
El sistema SHALL devolver para cada asignación en `mis-equipos` los datos del usuario (nombre, apellidos, email descifrado), el nombre del rol, el nombre del contexto (materia, carrera o cohorte según corresponda) y las fechas de vigencia.

#### Scenario: Respuesta con datos expandidos de materia
- **WHEN** un docente solicita `GET /api/equipos/mis-equipos` y tiene una asignación con `contexto_tipo == "Materia"`
- **THEN** la respuesta incluye `nombre_materia`, `codigo_materia`, `nombre_carrera`, `nombre_cohorte` (resueltos desde las FK)

#### Scenario: Respuesta con datos expandidos de cohorte
- **WHEN** un docente solicita `GET /api/equipos/mis-equipos` y tiene una asignación con `contexto_tipo == "Cohorte"`
- **THEN** la respuesta incluye `nombre_carrera` y `nombre_cohorte` (resueltos desde las FK), sin datos de materia

