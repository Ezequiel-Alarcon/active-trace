# umbral-materia Specification

## Purpose

Allow authorized users to configure approval thresholds per assignment (or per course as default). The threshold defines what grade values are considered "passing" so the system can derive the `aprobado` flag for any `Calificacion`.

## MODIFIED Requirements

### Requirement: UmbralMateria can be configured per asignacion with a default course-level fallback

The system SHALL store `UmbralMateria` records scoped by `(materia_id, asignacion_id)` where `asignacion_id` may be null (meaning "course-level default"). When deriving `aprobado` for a `Calificacion` with a given `asignacion_id`, the system SHALL use the assignment-specific threshold if one exists; otherwise, it SHALL fall back to the course-level default (where `asignacion_id IS NULL`).

#### Scenario: Deriving aprobado with textual nota in conjunto_aprobado

- **WHEN** `UmbralMateria` has `conjunto_aprobado=["Satisfactorio","Supera lo esperado"]`
- **AND** `Calificacion.nota = "Satisfactorio"` (string)
- **THEN** `aprobado = True`

#### Scenario: Deriving aprobado with textual nota not in conjunto_aprobado

- **WHEN** `UmbralMateria` has `conjunto_aprobado=["Satisfactorio","Supera lo esperado"]`
- **AND** `Calificacion.nota = "No Satisfactorio"`
- **THEN** `aprobado = False`

#### Scenario: Deriving aprobado with textual nota Supera lo esperado

- **WHEN** `UmbralMateria` has `conjunto_aprobado=["Satisfactorio","Supera lo esperado"]`
- **AND** `Calificacion.nota = "Supera lo esperado"`
- **THEN** `aprobado = True`

### Requirement: Default umbral is created when materia has no umbral configured

The system SHALL, when reading a `Calificacion` for a materia that has no `UmbralMateria` record (neither assignment-specific nor course-default), use a system-wide default of `umbral_pct=60` and `conjunto_aprobado=["Satisfactorio","Supera lo esperado"]`.

#### Scenario: Default umbral applied when no UmbralMateria exists

- **WHEN** `Calificacion` exists for `materia_id=M1` with `nota="Satisfactorio"`
- **AND** no `UmbralMateria` record exists for `materia_id=M1` (any asignacion)
- **THEN** `aprobado = True` (using default threshold 60 and default conjunto)

#### Scenario: Default umbral rejects non-passing textual nota

- **WHEN** `Calificacion` exists for `materia_id=M1` with `nota="No Satisfactorio"`
- **AND** no `UmbralMateria` record exists for `materia_id=M1`
- **THEN** `aprobado = False` (not in default conjunto ["Satisfactorio","Supera lo esperado"])

### Requirement: Derivation of aprobado uses escala_max to normalize threshold comparison

The system SHALL, when deriving `aprobado` for a numeric `Calificacion.nota`, compare the normalized percentage `(nota / escala_max * 100)` against `umbral_pct`. The `escala_max` parameter defaults to 10 and is passed explicitly by the caller (e.g., the import service or analisis service).

#### Scenario: Numeric nota above threshold in 0-10 scale passes

- **WHEN** `UmbralMateria` has `umbral_pct=60`, `escala_max=10`
- **AND** `Calificacion.nota = 7.5` (numeric)
- **THEN** `aprobado = True` (7.5/10*100 = 75 >= 60)

#### Scenario: Numeric nota below threshold in 0-10 scale fails

- **WHEN** `UmbralMateria` has `umbral_pct=70`, `escala_max=10`
- **AND** `Calificacion.nota = 6.0` (numeric)
- **THEN** `aprobado = False` (6.0/10*100 = 60 < 70)

#### Scenario: Numeric nota above threshold in 0-100 scale passes

- **WHEN** `UmbralMateria` has `umbral_pct=60`, `escala_max=100`
- **AND** `Calificacion.nota = 70` (numeric, 0-100 scale)
- **THEN** `aprobado = True` (70/100*100 = 70 >= 60)

#### Scenario: Numeric nota at exact threshold passes

- **WHEN** `UmbralMateria` has `umbral_pct=60`, `escala_max=10`
- **AND** `Calificacion.nota = 6.0`
- **THEN** `aprobado = True` (6.0/10*100 = 60 >= 60)
