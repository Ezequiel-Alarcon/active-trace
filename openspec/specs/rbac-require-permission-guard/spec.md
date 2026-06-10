# rbac-require-permission-guard Specification

## Purpose
TBD - created by archiving change rbac-permisos-finos. Update Purpose after archive.
## Requirements
### Requirement: Guard SHALL fail closed (403 if permission missing)

The guard SHALL return `403 Forbidden` when the user does NOT have the required permission.

#### Scenario: User without required permission gets 403

- **WHEN** user with effective permissions `{"avisos:confirmar", "atrasados:ver"}` calls endpoint decorated with `require_permission("calificaciones:importar")`
- **THEN** the response is `403 Forbidden` with `{"detail": "No tiene el permiso: calificaciones:importar"}`

#### Scenario: User with required permission passes guard

- **WHEN** user with effective permissions `{"calificaciones:importar", "atrasados:ver"}` calls endpoint decorated with `require_permission("calificaciones:importar")`
- **THEN** the response is the endpoint's normal result (permission granted)

### Requirement: Guard SHALL require an authenticated user before checking permissions

The guard SHALL return `401 Unauthorized` if the request has no valid authentication.

#### Scenario: Unauthenticated request gets 401 before permission check

- **WHEN** a request with no `Authorization` header calls an endpoint with `require_permission("calificaciones:importar")`
- **THEN** the response is `401 Unauthorized` with `{"detail": "No autenticado"}`
- **AND** no permission check is performed

### Requirement: Guard SHALL attach resolved permissions to request state

The guard SHALL attach resolved permissions to `request.state` for use by endpoint handlers.

#### Scenario: Endpoint handler accesses resolved permissions from request state

- **WHEN** `require_permission("auditoria:ver")` grants access
- **THEN** `request.state.current_user` contains the authenticated AuthUser
- **AND** `request.state.permissions` contains the resolved `set[str]` of effective permissions

### Requirement: Guard SHALL work with any permission string at runtime

The guard SHALL accept any `modulo:accion` string at runtime without static validation.

#### Scenario: Guard accepts non-seeded permission string without error

- **WHEN** endpoint declares `require_permission("custom:action")` (not in seeded permissions)
- **AND** user has no roles granting this permission
- **THEN** response is `403 Forbidden` (not a 500 error)
- **AND** if user happens to have it via a custom role, access is granted

### Requirement: System SHALL declare at least one require_permission on every protected endpoint

The system SHALL require every protected endpoint to declare at least one `require_permission(...)` dependency.

#### Scenario: Endpoint without permission declaration is inaccessible

- **WHEN** a new endpoint is registered WITHOUT `require_permission` decorator
- **AND** a request is made to that endpoint with a valid JWT
- **THEN** the response is `403 Forbidden` (or the auth layer returns 403 because no permission is declared)
- **AND** the endpoint CANNOT be accessed without explicitly declaring a permission

