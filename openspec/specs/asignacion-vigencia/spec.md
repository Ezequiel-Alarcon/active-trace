# asignacion-vigencia Specification

## Purpose
TBD - created by archiving change usuarios-y-asignaciones. Update Purpose after archive.
## Requirements
### Requirement: Asignacion SHALL computar estado_vigencia como derivado de desde/hasta

El sistema SHALL computar `estado_vigencia` como propiedad derivada:
- `Vigente` si `desde <= today()` AND (`hasta IS NULL OR hasta >= today()`)
- `Vencida` en caso contrario

El valor NO se persiste en base de datos. Se calcula al vuelo al leer la entidad.

#### Scenario: Asignación sin fecha hasta está Vigente

- **WHEN** una Asignacion tiene `desde=2026-01-01` y `hasta=NULL`
- **AND** la fecha actual es 2026-06-10
- **THEN** `estado_vigencia` es "Vigente"

#### Scenario: Asignación con hasta en el futuro está Vigente

- **WHEN** una Asignacion tiene `desde=2026-01-01` y `hasta=2026-12-31`
- **AND** la fecha actual es 2026-06-10
- **THEN** `estado_vigencia` es "Vigente"

#### Scenario: Asignación con hasta en el pasado está Vencida

- **WHEN** una Asignacion tiene `desde=2026-01-01` y `hasta=2026-05-31`
- **AND** la fecha actual es 2026-06-10
- **THEN** `estado_vigencia` es "Vencida"

#### Scenario: Asignación futura (desde > hoy) está Vencida

- **WHEN** una Asignacion tiene `desde=2026-09-01` y `hasta=NULL`
- **AND** la fecha actual es 2026-06-10
- **THEN** `estado_vigencia` es "Vencida" (aún no comenzó su vigencia)

#### Scenario: Asignación con desde = hoy está Vigente

- **WHEN** una Asignacion tiene `desde=2026-06-10` y `hasta=NULL`
- **AND** la fecha actual es 2026-06-10
- **THEN** `estado_vigencia` es "Vigente"

### Requirement: Asignación vencida SHALL conservarse pero no otorgar permisos

El sistema SHALL conservar las asignaciones vencidas en base de datos (no se eliminan automáticamente). La resolución de permisos efectivos (C-08 y posteriores) SHALL ignorar asignaciones con `estado_vigencia = Vencida`. El soft delete es el único mecanismo de borrado.

#### Scenario: Asignación vencida se conserva en DB

- **WHEN** una Asignacion alcanza su fecha `hasta` y queda Vencida
- **THEN** el registro permanece en la tabla `asignacion` con `deleted_at=NULL`
- **AND** aparece en consultas históricas

#### Scenario: Asignación vencida no se incluye en asignaciones vigentes

- **WHEN** un usuario tiene una Asignacion Vencida y una Vigente
- **AND** se consultan las asignaciones vigentes del usuario
- **THEN** solo se retorna la asignación Vigente

### Requirement: CRUD de asignación SHALL validar que desde <= hasta

El sistema SHALL validar al crear o actualizar una Asignacion que `desde` sea anterior o igual a `hasta` (si `hasta` no es null). Si la validación falla, el sistema retorna 422 Unprocessable Entity.

#### Scenario: Crear asignación con desde > hasta es rechazada

- **WHEN** se envía `POST /api/asignaciones` con `{"desde": "2026-12-01", "hasta": "2026-01-01", ...}`
- **THEN** el sistema retorna 422 con mensaje indicando que `desde` debe ser anterior a `hasta`

#### Scenario: Actualizar asignación con desde > hasta es rechazada

- **WHEN** una Asignacion existente se actualiza con `{"hasta": "2025-01-01"}` y su `desde` es 2026-01-01
- **THEN** el sistema retorna 422

### Requirement: Asignación SHALL ser creada y gestionada con permiso `equipos:asignar`

El sistema SHALL exponer endpoints CRUD en `/api/asignaciones` protegidos con el permiso `equipos:asignar` (roles COORDINADOR, ADMIN).

#### Scenario: COORDINADOR crea asignación exitosamente

- **WHEN** un usuario con rol COORDINADOR envía `POST /api/asignaciones` con datos válidos
- **THEN** el sistema crea la Asignacion y retorna 201

#### Scenario: PROFESOR sin permiso recibe 403

- **WHEN** un usuario con rol PROFESOR (sin `equipos:asignar`) envía `POST /api/asignaciones`
- **THEN** el sistema retorna 403 Forbidden

### Requirement: Asignación SHALL usar soft delete

El sistema SHALL implementar `DELETE /api/asignaciones/{id}` como soft delete (setea `deleted_at`). No se permite hard delete en flujo normal.

#### Scenario: Soft delete de asignación

- **WHEN** un COORDINADOR hace `DELETE /api/asignaciones/{id}`
- **THEN** la asignación se marca con `deleted_at` y retorna 204
- **AND** la asignación ya no aparece en listados

