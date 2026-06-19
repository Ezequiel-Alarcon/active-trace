## MODIFIED Requirements

### Requirement: Guard SHALL fail closed (403 if permission missing)

**Change**: The guard MUST be wired as a FastAPI dependency via `Depends()` in the route decorator's `dependencies` parameter. A bare `require_permission("...")` call that is not wrapped in `Depends()` MUST NOT execute the permission check.

The guard SHALL return `403 Forbidden` when the user does NOT have the required permission.

#### Scenario: User without required permission gets 403

- **WHEN** a route is declared with `dependencies=[Depends(require_permission("calificaciones:importar"))]`
- **AND** user with effective permissions `{"avisos:confirmar", "atrasados:ver"}` calls this endpoint
- **THEN** the response is `403 Forbidden` with `{"detail": "No tiene el permiso: calificaciones:importar"}`

#### Scenario: Bare require_permission without Depends does NOT enforce the check

- **WHEN** a route is declared with `require_permission("calificaciones:importar")` (no `Depends()` wrapper)
- **THEN** any authenticated user can access the endpoint regardless of permissions
- **AND** the test suite SHALL verify that every `require_permission` call is wrapped in `Depends()`

### Requirement: Every protected endpoint SHALL use dependencies=[Depends(require_permission(...))]

Every router that currently uses bare `require_permission("...")` calls SHALL be fixed to use the `dependencies=[Depends(...)]` decorator pattern. This applies to 4 files:

- `app/api/v1/analisis.py` (4 calls)
- `app/api/v1/calificaciones.py` (5 calls)
- `app/api/v1/umbral_materia.py` (3 calls)
- `app/modules/comunicacion/router.py` (6 calls)

#### Scenario: All 4 router files use Depends after fix

- **WHEN** scanning `app/api/v1/analisis.py`, `app/api/v1/calificaciones.py`, `app/api/v1/umbral_materia.py`, and `app/modules/comunicacion/router.py`
- **THEN** every `require_permission` call is wrapped in `Depends()`
- **AND** no bare `require_permission("...")` call exists outside of the `app/rbac/` module itself
