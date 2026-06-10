# asignacion-contexto Specification

## Purpose

Define el comportamiento de acotamiento contextual de las asignaciones: el enum `contexto_tipo` (Global, Carrera, Cohorte, Materia), la FK polimórfica `contexto_id`, la jerarquía de `responsable_id`, y las validaciones de integridad referencial contra las entidades de C-06.

## ADDED Requirements

### Requirement: Asignacion SHALL acotarse a un contexto mediante `contexto_tipo` y `contexto_id`

El sistema SHALL soportar cuatro tipos de contexto para una Asignacion: `Global` (sin scope, `contexto_id=NULL`), `Carrera`, `Cohorte`, y `Materia` (con `contexto_id` apuntando a la entidad correspondiente). El par `(contexto_tipo, contexto_id)` define el alcance de la asignación.

#### Scenario: Asignación global sin contexto_id

- **WHEN** se crea una Asignacion con `contexto_tipo=Global` y `contexto_id=NULL`
- **THEN** el sistema persiste la asignación con `contexto_id=NULL`
- **AND** la asignación aplica a todo el tenant sin restricción de scope

#### Scenario: Asignación a una Carrera específica

- **WHEN** se crea una Asignacion con `contexto_tipo=Carrera` y `contexto_id=<id de carrera existente>`
- **THEN** el sistema persiste la asignación con el `contexto_id` provisto
- **AND** la asignación solo aplica dentro de esa carrera

#### Scenario: Asignación a una Cohorte específica

- **WHEN** se crea una Asignacion con `contexto_tipo=Cohorte` y `contexto_id=<id de cohorte existente>`
- **THEN** el sistema persiste la asignación con el `contexto_id` provisto

#### Scenario: Asignación a una Materia específica

- **WHEN** se crea una Asignacion con `contexto_tipo=Materia` y `contexto_id=<id de materia existente>`
- **THEN** el sistema persiste la asignación con el `contexto_id` provisto

### Requirement: Sistema SHALL validar integridad referencial del contexto contra entidades existentes

El sistema SHALL validar al crear o actualizar una Asignacion que, si `contexto_tipo != Global`, la entidad referenciada por `contexto_id` exista y esté activa (no soft-deleted) en el mismo tenant. Si la validación falla, retorna 422.

#### Scenario: Contexto Carrera inexistente es rechazado

- **WHEN** se crea una Asignacion con `contexto_tipo=Carrera` y `contexto_id=<UUID inexistente>`
- **THEN** el sistema retorna 422 con mensaje indicando que la carrera no existe

#### Scenario: Contexto Materia soft-deleted es rechazada

- **WHEN** se crea una Asignacion con `contexto_tipo=Materia` y `contexto_id=<id de materia soft-deleted>`
- **THEN** el sistema retorna 422 con mensaje indicando que la materia no está disponible

#### Scenario: Contexto Cohorte de otro tenant es rechazado

- **WHEN** se crea una Asignacion en tenant A con `contexto_tipo=Cohorte` y `contexto_id=<id de cohorte de tenant B>`
- **THEN** el sistema retorna 422 (o 404) porque la cohorte no pertenece al tenant de la asignación

### Requirement: Asignacion SHALL soportar jerarquía mediante `responsable_id`

El sistema SHALL permitir que una Asignacion referencie a otro Usuario como responsable mediante `responsable_id` (FK a `usuario.id`, nullable). Esto establece una relación jerárquica (ej: PROFESOR → COORDINADOR como responsable).

#### Scenario: Asignación con responsable

- **WHEN** se crea una Asignacion con `responsable_id=<id de otro Usuario>`
- **THEN** la asignación queda vinculada jerárquicamente a ese responsable
- **AND** `responsable_id` es nullable (puede ser NULL)

#### Scenario: Responsable inexistente es rechazado

- **WHEN** se crea una Asignacion con `responsable_id=<UUID inexistente>`
- **THEN** el sistema retorna 422 con mensaje indicando que el responsable no existe

#### Scenario: Asignación sin responsable

- **WHEN** se crea una Asignacion sin `responsable_id` (o con `null`)
- **THEN** la asignación se crea exitosamente sin jerarquía

### Requirement: Asignacion SHALL listarse con filtro por contexto

El sistema SHALL soportar filtros en `GET /api/asignaciones` por `contexto_tipo` y `contexto_id` para que un coordinador pueda ver todas las asignaciones de una carrera, cohorte o materia específica.

#### Scenario: Listar asignaciones de una carrera

- **WHEN** un COORDINADOR hace `GET /api/asignaciones?contexto_tipo=Carrera&contexto_id=<id>`
- **THEN** el sistema retorna solo las asignaciones con ese `contexto_tipo` y `contexto_id`

#### Scenario: Listar asignaciones de un usuario con su contexto incluido

- **WHEN** se lista una Asignacion en la respuesta
- **THEN** la respuesta incluye `contexto_tipo` y `contexto_id`
- **AND** el contexto se resuelve a su representación (ej: nombre de la carrera) si el frontend lo requiere

### Requirement: Asignacion SHALL validar que usuario_id y rol_id existen en el tenant

El sistema SHALL validar al crear o actualizar una Asignacion que `usuario_id` y `rol_id` referencien entidades existentes, activas (no soft-deleted), y del mismo tenant.

#### Scenario: Usuario soft-deleted no puede ser asignado

- **WHEN** se crea una Asignacion con `usuario_id=<id de usuario soft-deleted>`
- **THEN** el sistema retorna 422 con mensaje indicando que el usuario no está disponible

#### Scenario: Rol de otro tenant no puede ser asignado

- **WHEN** se crea una Asignacion en tenant A con `rol_id=<id de rol de tenant B>`
- **THEN** el sistema retorna 422 (el repositorio tenant-scoped no encuentra el rol)
