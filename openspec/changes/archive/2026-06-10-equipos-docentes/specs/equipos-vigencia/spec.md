## ADDED Requirements

### Requirement: Modificar vigencia general del equipo
El sistema SHALL permitir a un COORDINADOR o ADMIN actualizar en bloque las fechas `desde` y `hasta` de todas las asignaciones vigentes que coincidan con los filtros de `materia_id`, `cohorte_id` y opcionalmente `rol_id`.

#### Scenario: Modificar vigencia de equipo por materia y cohorte
- **WHEN** un COORDINADOR envía `PATCH /api/equipos/vigencia` con `materia_id`, `cohorte_id`, `desde` y `hasta` nuevos, y existen 10 asignaciones vigentes que coinciden
- **THEN** el sistema actualiza las 10 asignaciones, devuelve `actualizadas: 10` y emite evento de auditoría `ASIGNACION_MODIFICAR`

#### Scenario: Modificar vigencia filtrando también por rol
- **WHEN** un COORDINADOR envía `PATCH /api/equipos/vigencia` con `materia_id`, `cohorte_id`, `rol_id`, `desde` y `hasta`, y existen 10 asignaciones vigentes (5 del rol especificado, 5 de otro rol)
- **THEN** el sistema solo actualiza las 5 del rol especificado

#### Scenario: Modificar vigencia no afecta asignaciones vencidas
- **WHEN** un COORDINADOR envía `PATCH /api/equipos/vigencia` para una materia×cohorte donde hay 5 asignaciones vigentes y 3 vencidas
- **THEN** el sistema solo actualiza las 5 vigentes, las 3 vencidas permanecen sin cambios

#### Scenario: Modificar vigencia sin asignaciones que coincidan
- **WHEN** un COORDINADOR envía `PATCH /api/equipos/vigencia` con filtros que no matchean ninguna asignación vigente
- **THEN** el sistema devuelve `actualizadas: 0` con status 200

#### Scenario: Modificar vigencia con fechas inválidas
- **WHEN** un COORDINADOR envía `PATCH /api/equipos/vigencia` con `hasta` anterior a `desde`
- **THEN** el sistema devuelve 422 con detalle "hasta debe ser posterior a desde"

#### Scenario: Modificar vigencia sin materia_id
- **WHEN** un COORDINADOR envía `PATCH /api/equipos/vigencia` sin `materia_id`
- **THEN** el sistema devuelve 422 con detalle indicando que `materia_id` es requerido

#### Scenario: Modificar vigencia sin permisos
- **WHEN** un PROFESOR autenticado envía `PATCH /api/equipos/vigencia`
- **THEN** el sistema devuelve 403 Forbidden

### Requirement: Validación de entidades en modificación de vigencia
El sistema SHALL validar que `materia_id`, `cohorte_id` y `rol_id` (si se proporciona) existan en el tenant antes de realizar la modificación en bloque.

#### Scenario: Materia inexistente en modificación de vigencia
- **WHEN** un COORDINADOR envía `PATCH /api/equipos/vigencia` con un `materia_id` inexistente
- **THEN** el sistema devuelve 422 con detalle "La materia especificada no existe"
