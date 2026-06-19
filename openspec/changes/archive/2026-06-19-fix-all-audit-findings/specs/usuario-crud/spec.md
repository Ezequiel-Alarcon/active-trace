## MODIFIED Requirements

### Requirement: Usuario model SHALL include an `estado` field

**Change**: The `Usuario` model currently lacks an `estado` field. A new field `estado` SHALL be added to track the user's status (e.g., `activo`, `inactivo`, `suspendido`). The field SHALL default to `activo` for backward compatibility with existing rows.

#### Scenario: Creating a Usuario without estado defaults to activo

- **WHEN** a `Usuario` is created without specifying `estado`
- **THEN** the stored row has `estado = "activo"`

#### Scenario: Setting estado to inactivo excludes user from active queries

- **WHEN** a `Usuario` has `estado = "inactivo"`
- **THEN** the user SHALL NOT be returned by default active-user queries
- **AND** the user SHALL NOT be able to authenticate (login returns `AUTH_INVALID_CREDENTIALS`)
