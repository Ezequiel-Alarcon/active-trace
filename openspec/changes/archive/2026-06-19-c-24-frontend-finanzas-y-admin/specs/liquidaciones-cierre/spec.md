# liquidaciones-cierre Specification

## ADDED Requirements

### Requirement: Cerrar liquidación del período
The system SHALL allow a FINANZAS user to close (inmutabilize) a period's liquidation. Once closed, no further modifications are possible (enforced by backend).

#### Scenario: Close liquidation via confirmation dialog
- **WHEN** a user with `liquidaciones:cerrar` clicks "Cerrar liquidación" on the period view
- **THEN** the system shows a confirmation dialog with text "¿Está seguro de cerrar la liquidación del período? Esta acción es irreversible."
- **AND** the confirm button shows "Cerrar liquidación" (danger variant)
- **AND** the cancel button dismisses the dialog

#### Scenario: Confirm close calls API and shows success
- **WHEN** the user confirms the close dialog
- **THEN** the system calls `POST /api/liquidaciones/cerrar` with the current periodo
- **AND** on 200, shows a success toast "Liquidación cerrada correctamente"
- **AND** disables the close button and marks the period as "Cerrada" in the UI

#### Scenario: Close API error shows error
- **WHEN** the close API returns an error
- **THEN** the system shows an error toast with the API error message
- **AND** the liquidation remains open (UI state reverts)

#### Scenario: Already closed liquidation hides close button
- **WHEN** the period is already closed (GET /api/liquidaciones returns `estado: "Cerrada"`)
- **THEN** the "Cerrar liquidación" button is not rendered
- **AND** a StatusBadge with estado "Cerrada" is shown
