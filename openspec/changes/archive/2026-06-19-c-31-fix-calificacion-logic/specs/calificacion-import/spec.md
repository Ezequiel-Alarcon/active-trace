# calificacion-import Specification

## Purpose

Allow authorized users to import grades from LMS (Moodle) into the system via a two-step flow: preview without persisting, then confirm to persist. Also supports importing completion reports (TPs without a grade, stored as `nota = null`). Every import is audited with the operator, timestamp, and import batch ID.

## ADDED Requirements

### Requirement: Column headers ending with (Real) are detected as numeric grade columns

The system SHALL detect any column header that ends with `(Real)` (case-insensitive) as a numeric grade column. This includes but is not limited to exact aliases like `"nota (real)"` or `"calificacion (real)"` — headers such as `"Mi Nota (Real)"`, `"Calificación Final (Real)"`, or `"Grade (Real)"` SHALL also be detected as numeric grade columns per RN-01.

#### Scenario: Header with custom prefix ending in (Real) is detected as numeric

- **WHEN** user uploads a CSV with header `"Mi Nota (Real)"`
- **THEN** the column is recognized as a numeric grade column and parsed as `nota`

#### Scenario: Header Calificacion Final (Real) is detected as numeric

- **WHEN** user uploads an Excel file with header `"Calificación Final (Real)"`
- **THEN** the column is recognized as a numeric grade column and parsed as `nota`

#### Scenario: Exact alias nota (real) still works

- **WHEN** user uploads a file with header `"nota (real)"`
- **THEN** the column is recognized as numeric grade (existing alias still functions)

#### Scenario: Non-(Real) columns are not detected as numeric regardless of prefix

- **WHEN** user uploads a file with header `"Mi Nota"`
- **THEN** the column is NOT treated as a numeric grade column
