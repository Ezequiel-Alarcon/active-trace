# Capability: `audit-log-impersonation`

> Impersonation session management. When a user with `impersonacion:usar` starts impersonating another user, every audited action records both the real actor (`actor_id`) and the impersonated user (`impersonado_id`). `IMPERSONACION_INICIAR` and `IMPERSONACION_FINALIZAR` are recorded as special audit entries.

## ADDED Requirements

### Requirement: System SHALL require impersonacion:usar to start impersonation

The system SHALL only allow a user to start an impersonation session if they have the `impersonacion:usar` permission. Requests without this permission SHALL receive `403 Forbidden`.

#### Scenario: User without impersonacion:usar cannot start impersonation

- **WHEN** user without `impersonacion:usar` calls `POST /api/impersonation/start` with `{target_user_id: ...}`
- **THEN** the response is `403 Forbidden` with `{"detail": "No tiene el permiso: impersonacion:usar"}`

### Requirement: System SHALL create IMPERSONACION_INICIAR audit entry when impersonation starts

The system SHALL write an AuditLog entry with `accion = "IMPERSONACION_INICIAR"` when an impersonation session starts. The entry SHALL record the real actor as `actor_id` and the target user as `impersonado_id`.

#### Scenario: Starting impersonation creates audit entry

- **WHEN** admin calls `POST /api/impersonation/start` with `{target_user_id: U2}`
- **AND** the admin's user ID is U1
- **THEN** an AuditLog entry is created with `actor_id = U1`, `impersonado_id = U2`, `accion = "IMPERSONACION_INICIAR"`
- **AND** `tenant_id` is set to the current tenant

### Requirement: System SHALL create IMPERSONACION_FINALIZAR audit entry when impersonation ends

The system SHALL write an AuditLog entry with `accion = "IMPERSONACION_FINALIZAR"` when the impersonation session ends.

#### Scenario: Ending impersonation creates audit entry

- **WHEN** admin calls `DELETE /api/impersonation/end`
- **THEN** an AuditLog entry is created with `accion = "IMPERSONACION_FINALIZAR"`
- **AND** `actor_id` is the real admin, `impersonado_id` is the previously impersonated user

### Requirement: While impersonating, all audited actions SHALL record impersonado_id

The system SHALL set `impersonado_id` on every AuditLog entry created during an active impersonation session. The `actor_id` remains the real user; `impersonado_id` is the user being impersonated.

#### Scenario: Audited action during impersonation records impersonado_id

- **WHEN** admin U1 is impersonating user U2
- **AND** admin U1 performs an action (e.g., via a service method decorated with `@audit("USUARIOS_GESTIONAR")`)
- **THEN** the resulting AuditLog entry has `actor_id = U1` (real actor) AND `impersonado_id = U2` (impersonated user)
- **AND** `accion = "USUARIOS_GESTIONAR"`

### Requirement: Impersonation context SHALL be stored server-side in request state

The impersonation state SHALL be stored in `request.state.impersonating` (bool) and `request.state.impersonated_user_id` (UUID). The state is set by `POST /api/impersonation/start` and cleared by `DELETE /api/impersonation/end`. The JWT does not carry impersonation state.

#### Scenario: Impersonation state is available in request state

- **WHEN** a request is made after `POST /api/impersonation/start {target_user_id: U2}`
- **THEN** `request.state.impersonating == True`
- **AND** `request.state.impersonated_user_id == U2`

### Requirement: System SHALL clear impersonation state when session ends

When `DELETE /api/impersonation/end` is called, the impersonation state SHALL be cleared from the request context. Subsequent audited actions SHALL have `impersonado_id = NULL`.

#### Scenario: After ending impersonation, impersonado_id is NULL

- **WHEN** admin calls `DELETE /api/impersonation/end`
- **AND** admin performs a subsequent audited action
- **THEN** the resulting AuditLog entry has `impersonado_id = NULL`