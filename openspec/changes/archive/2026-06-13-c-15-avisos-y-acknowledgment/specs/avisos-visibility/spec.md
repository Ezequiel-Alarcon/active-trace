# avisos-visibility Specification

## ADDED Requirements

### Requirement: User sees only visible avisos

The system SHALL return only avisos where the authenticated user matches the audience segmentation and the aviso is within its visibility window. The query SHALL filter by: `activo=true`, `inicio_en <= now()`, `fin_en >= now()`.

#### Scenario: User sees Global avisos
- **WHEN** any authenticated user sends `GET /api/avisos/mis-avisos` and there is a Global aviso within its visibility window
- **THEN** the Global aviso is included in the response

#### Scenario: User does not see expired avisos
- **WHEN** an authenticated user sends `GET /api/avisos/mis-avisos` and there is an aviso with `fin_en` in the past
- **THEN** the expired aviso is NOT included in the response

#### Scenario: User does not see future avisos
- **WHEN** an authenticated user sends `GET /api/avisos/mis-avisos` and there is an aviso with `inicio_en` in the future
- **THEN** the future aviso is NOT included in the response

#### Scenario: User does not see inactive avisos
- **WHEN** an authenticated user sends `GET /api/avisos/mis-avisos` and there is an aviso with `activo=false`
- **THEN** the inactive aviso is NOT included in the response

### Requirement: Avisos filtered by alcance PorRol

The system SHALL show avisos with `alcance=PorRol` only to users whose role matches `rol_destino`. If `rol_destino` is null, the aviso SHALL be visible to all roles.

#### Scenario: PROFESOR sees PorRol aviso for PROFESOR
- **WHEN** a PROFESOR sends `GET /api/avisos/mis-avisos` and there is a PorRol aviso with `rol_destino=PROFESOR`
- **THEN** the aviso is included in the response

#### Scenario: ALUMNO does not see PorRol aviso for PROFESOR
- **WHEN** an ALUMNO sends `GET /api/avisos/mis-avisos` and there is a PorRol aviso with `rol_destino=PROFESOR`
- **THEN** the aviso is NOT included in the response

#### Scenario: PorRol aviso with null rol_destino visible to all
- **WHEN** any user sends `GET /api/avisos/mis-avisos` and there is a PorRol aviso with `rol_destino=null`
- **THEN** the aviso is included in the response

### Requirement: Avisos filtered by alcance PorMateria

The system SHALL show avisos with `alcance=PorMateria` only to users assigned to the referenced materia. The user's materia assignments are determined from the Asignacion table (active, non-deleted).

#### Scenario: PROFESOR sees PorMateria aviso for their materia
- **WHEN** a PROFESOR assigned to materia X sends `GET /api/avisos/mis-avisos` and there is a PorMateria aviso with `materia_id=X`
- **THEN** the aviso is included in the response

#### Scenario: PROFESOR does not see PorMateria aviso for unassigned materia
- **WHEN** a PROFESOR not assigned to materia X sends `GET /api/avisos/mis-avisos` and there is a PorMateria aviso with `materia_id=X`
- **THEN** the aviso is NOT included in the response

### Requirement: Avisos filtered by alcance PorCohorte

The system SHALL show avisos with `alcance=PorCohorte` only to users assigned to the referenced cohorte.

#### Scenario: ALUMNO sees PorCohorte aviso for their cohorte
- **WHEN** an ALUMNO in cohorte Y sends `GET /api/avisos/mis-avisos` and there is a PorCohorte aviso with `cohorte_id=Y`
- **THEN** the aviso is included in the response

### Requirement: Avisos sorted by orden then created_at

The system SHALL return visible avisos sorted by `orden` ascending (lower number = higher priority), and for equal orden, by `created_at` descending (newer first).

#### Scenario: Avisos are returned in correct order
- **WHEN** a user sends `GET /api/avisos/mis-avisos` and there are multiple matching avisos
- **THEN** avisos with lower `orden` appear first; avisos with same `orden` appear with newest first
