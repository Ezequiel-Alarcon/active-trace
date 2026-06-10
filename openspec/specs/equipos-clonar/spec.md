# equipos-clonar Specification

## Purpose
TBD - created by archiving change equipos-docentes. Update Purpose after archive.
## Requirements
### Requirement: Clonar equipo docente entre cohortes (RN-12)
El sistema SHALL permitir a un COORDINADOR o ADMIN duplicar todas las asignaciones vigentes de una cohorte origen a una cohorte destino, copiando `usuario_id`, `rol_id` y ajustando `contexto_id` al nuevo cohorte cuando corresponda, con nuevas fechas de vigencia `desde` y `hasta`.

#### Scenario: Clonado exitoso de equipo entre cohortes
- **WHEN** un COORDINADOR envía `POST /api/equipos/clonar` con `cohorte_origen_id`, `cohorte_destino_id`, `desde` y `hasta` válidos, y la cohorte origen tiene 5 asignaciones vigentes
- **THEN** el sistema crea 5 nuevas asignaciones en el destino, devuelve `creadas: 5, omitidas: 0, fallidas: 0`, y emite evento de auditoría `ASIGNACION_MODIFICAR`

#### Scenario: Clonado omite asignaciones ya existentes en destino
- **WHEN** un COORDINADOR clona un equipo y una asignación (mismo usuario+rol+contexto) ya existe en la cohorte destino
- **THEN** el sistema omite esa asignación, la cuenta en `omitidas`, y continúa con las demás

#### Scenario: Clonado con cohorte origen inexistente
- **WHEN** un COORDINADOR envía `POST /api/equipos/clonar` con un `cohorte_origen_id` inexistente
- **THEN** el sistema devuelve 422 con detalle "La cohorte origen especificada no existe"

#### Scenario: Clonado con cohorte destino inexistente
- **WHEN** un COORDINADOR envía `POST /api/equipos/clonar` con un `cohorte_destino_id` inexistente
- **THEN** el sistema devuelve 422 con detalle "La cohorte destino especificada no existe"

#### Scenario: Clonado con fechas inválidas
- **WHEN** un COORDINADOR envía `POST /api/equipos/clonar` con `hasta` anterior a `desde`
- **THEN** el sistema devuelve 422 con detalle "hasta debe ser posterior a desde"

#### Scenario: Rollback manual ante error inesperado
- **WHEN** durante el clonado ocurre un error inesperado en la asignación N (ej: violación de integridad por datos corruptos)
- **THEN** el sistema hace soft-delete de las N-1 asignaciones ya creadas en este lote, y devuelve `creadas: 0, fallidas: [{asignacion_origen_id, motivo}]`

#### Scenario: Cohorte origen sin asignaciones vigentes
- **WHEN** un COORDINADOR envía `POST /api/equipos/clonar` y la cohorte origen no tiene asignaciones vigentes
- **THEN** el sistema devuelve `creadas: 0, omitidas: 0, fallidas: 0` con status 200

### Requirement: Ajuste de contexto en clonado
El sistema SHALL ajustar el `contexto_id` de las asignaciones clonadas: si el `contexto_tipo` es "Cohorte", `contexto_id` se reemplaza por el `cohorte_destino_id`. Si el `contexto_tipo` es "Materia", se mantiene el `contexto_id` original.

#### Scenario: Clonado ajusta contexto de tipo Cohorte
- **WHEN** se clona una asignación con `contexto_tipo == "Cohorte"` y `contexto_id == <origen>`
- **THEN** la nueva asignación en destino tiene `contexto_id == <destino>`

#### Scenario: Clonado mantiene contexto de tipo Materia
- **WHEN** se clona una asignación con `contexto_tipo == "Materia"` y `contexto_id == <materia_id>`
- **THEN** la nueva asignación en destino mantiene `contexto_id == <materia_id>`

