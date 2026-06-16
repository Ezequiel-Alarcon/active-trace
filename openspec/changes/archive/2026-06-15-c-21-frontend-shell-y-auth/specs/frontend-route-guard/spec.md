## ADDED Requirements

### Requirement: Unauthenticated access to protected routes redirects to login

The system SHALL provide a `RequireAuth` route wrapper. When no authenticated session is present, it MUST redirect to `/login` (preserving the attempted location so the user can be returned after login). While the session bootstrap is in flight, it MUST render a loading state rather than redirecting prematurely.

#### Scenario: No session redirects to login

- **WHEN** an unauthenticated user navigates to a protected route
- **THEN** the app redirects to `/login`
- **AND** the originally attempted location is preserved for post-login return

#### Scenario: Bootstrap-in-progress shows loading, not a redirect

- **WHEN** the session bootstrap is still in flight on app start
- **THEN** a loading state is rendered
- **AND** no premature redirect to `/login` occurs until the bootstrap resolves

### Requirement: Routes are guarded by a fine-grained permission and are fail-closed

The system SHALL provide a `RequirePermission` wrapper that takes a `modulo:accion` permission string. It MUST render the route content only if the session's effective permissions include that exact permission; otherwise it MUST render the `Forbidden403` page. Absence of the required permission MUST block access (fail-closed) — no permission is granted by default.

#### Scenario: User with the required permission sees the route

- **WHEN** an authenticated user whose effective permissions include `calificaciones:importar` reaches a route guarded by `RequirePermission perm="calificaciones:importar"`
- **THEN** the route content is rendered

#### Scenario: User without the required permission is blocked (fail-closed)

- **WHEN** an authenticated user whose effective permissions do NOT include `liquidaciones:cerrar` reaches a route guarded by `RequirePermission perm="liquidaciones:cerrar"`
- **THEN** the `Forbidden403` page is rendered
- **AND** the route content is not rendered

#### Scenario: An empty permission set blocks every guarded route

- **WHEN** an authenticated user whose effective permissions array is empty reaches any permission-guarded route
- **THEN** the `Forbidden403` page is rendered (no route is accessible without an explicit permission)

### Requirement: The navigation menu shows only items the session is permitted to use

The system SHALL render navigation menu items conditionally based on the session's effective permissions via a `hasPermission(perm)` helper. A menu item whose required permission is not in the session MUST NOT be rendered. This is defense-in-depth alongside the route guard; it MUST NOT be the only access control.

#### Scenario: Menu hides items the user cannot access

- **WHEN** the authenticated session's effective permissions include `atrasados:ver` but not `liquidaciones:calcular`
- **THEN** the menu renders the item guarded by `atrasados:ver`
- **AND** the menu does not render the item guarded by `liquidaciones:calcular`

#### Scenario: hasPermission returns false for a permission not in the session

- **WHEN** `hasPermission("auditoria:ver")` is called for a session whose effective permissions do not include it
- **THEN** it returns `false`
