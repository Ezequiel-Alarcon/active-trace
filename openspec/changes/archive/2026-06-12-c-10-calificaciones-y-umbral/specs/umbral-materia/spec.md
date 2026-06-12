# umbral-materia Specification

## Purpose

Allow authorized users to configure approval thresholds per assignment (or per course as default). The threshold defines what grade values are considered "passing" so the system can derive the `aprobado` flag for any `Calificacion`.

## ADDED Requirements

### Requirement: UmbralMateria can be configured per asignacion with a default course-level fallback

The system SHALL store `UmbralMateria` records scoped by `(materia_id, asignacion_id)` where `asignacion_id` may be null (meaning "course-level default"). When deriving `aprobado` for a `Calificacion` with a given `asignacion_id`, the system SHALL use the assignment-specific threshold if one exists; otherwise, it SHALL fall back to the course-level default (where `asignacion_id IS NULL`).

#### Scenario: Assignment-specific threshold takes precedence over course default

- **WHEN** there exists `UmbralMateria` with `materia_id=M1`, `asignacion_id=A1`, `umbral_pct=70`
- **AND** there exists `UmbralMateria` with `materia_id=M1`, `asignacion_id=null`, `umbral_pct=60`
- **AND** user queries `aprobado` for a `Calificacion` with `materia_id=M1` and `asignacion_id=A1`
- **THEN** the threshold `70` is used

#### Scenario: Course default used when no assignment-specific threshold exists

- **WHEN** there exists `UmbralMateria` with `materia_id=M1`, `asignacion_id=null`, `umbral_pct=60`
- **AND** user queries `aprobado` for a `Calificacion` with `materia_id=M1` and `asignacion_id=A2` (no specific threshold for A2)
- **THEN** the threshold `60` is used

#### Scenario: Deriving aprobado with numeric nota above threshold

- **WHEN** `UmbralMateria` has `umbral_pct=60`
- **AND** `Calificacion.nota = 7.5` (numeric)
- **THEN** `aprobado = True`

#### Scenario: Deriving aprobado with numeric nota below threshold

- **WHEN** `UmbralMateria` has `umbral_pct=70`
- **AND** `Calificacion.nota = 6.0` (numeric)
- **THEN** `aprobado = False`

#### Scenario: Deriving aprobado with textual nota in conjunto_aprobado

- **WHEN** `UmbralMateria` has `conjunto_aprobado=["A","B+","C","7","8","9","10"]`
- **AND** `Calificacion.nota = "A"` (string)
- **THEN** `aprobado = True`

#### Scenario: Deriving aprobado with textual nota not in conjunto_aprobado

- **WHEN** `UmbralMateria` has `conjunto_aprobado=["A","B+","C","7","8","9","10"]`
- **AND** `Calificacion.nota = "D"`
- **THEN** `aprobado = False`

#### Scenario: Deriving aprobado with list nota (any item in conjunto)

- **WHEN** `UmbralMateria` has `conjunto_aprobado=["A","B+","C"]`
- **AND** `Calificacion.nota = ["A", "D"]` (list)
- **THEN** `aprobado = True` (because "A" is in conjunto)

#### Scenario: Deriving aprobado with null nota returns False

- **WHEN** `Calificacion.nota = null`
- **THEN** `aprobado = False` regardless of threshold configuration

### Requirement: Default umbral is created when materia has no umbral configured

The system SHALL, when reading a `Calificacion` for a materia that has no `UmbralMateria` record (neither assignment-specific nor course-default), use a system-wide default of `umbral_pct=60` and `conjunto_aprobado=["A","B+","C","7","8","9","10"]`.

#### Scenario: Default umbral applied when no UmbralMateria exists

- **WHEN** `Calificacion` exists for `materia_id=M1` with `nota=7`
- **AND** no `UmbralMateria` record exists for `materia_id=M1` (any asignacion)
- **THEN** `aprobado = True` (using default threshold 60)

### Requirement: CRUD for UmbralMateria with tenant isolation

The system SHALL allow users with `calificaciones:importar` to create, update, and list `UmbralMateria` records scoped to their tenant. All queries filter by `tenant_id` from JWT.

#### Scenario: Create umbral for specific assignment

- **WHEN** user with `calificaciones:importar` calls `POST /api/umbral-materia` with `materia_id=M1`, `asignacion_id=A1`, `umbral_pct=70`, `conjunto_aprobado=["A","B","C"]`
- **THEN** response is `201 Created` with the created `UmbralMateria`
- **AND** subsequent `GET /api/umbral-materia?materia_id=M1` returns this record

#### Scenario: Update existing umbral

- **WHEN** user calls `PUT /api/umbral-materia/{id}` with `umbral_pct=75`
- **THEN** response is `200 OK` with updated record
- **AND** existing `Calificacion` records are NOT modified (aprobado is re-derived on read)

#### Scenario: List umbral excludes soft-deleted records

- **WHEN** admin soft-deletes an `UmbralMateria` record
- **AND** user calls `GET /api/umbral-materia`
- **THEN** the soft-deleted record is not returned

#### Scenario: Tenant isolation on umbral queries

- **WHEN** tenant A has an `UmbralMateria` for `materia_id=M1`
- **AND** tenant B queries `GET /api/umbral-materia?materia_id=M1`
- **THEN** tenant B sees no records for `M1`

### Requirement: UmbralMateria requires calificaciones:importar for mutations

The system SHALL deny `POST` and `PUT` on `/api/umbral-materia` for users without `calificaciones:importar`.

#### Scenario: User without permission cannot create umbral

- **WHEN** user WITHOUT `calificaciones:importar` calls `POST /api/umbral-materia`
- **THEN** response is `403 Forbidden`

### Requirement: Unique constraint on materia_id + asignacion_id (excluding soft-deleted)

The combination `(materia_id, asignacion_id)` SHALL be unique per tenant, excluding soft-deleted records.

#### Scenario: Duplicate umbral for same materia and asignacion is rejected

- **WHEN** user creates `UmbralMateria` with `materia_id=M1`, `asignacion_id=A1`
- **AND** user attempts to create another `UmbralMateria` with the same `materia_id=M1` and `asignacion_id=A1`
- **THEN** response is `409 Conflict` with `{"detail": "Ya existe un umbral para esta materia y asignación"}`