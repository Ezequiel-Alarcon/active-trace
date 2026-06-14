## Why

Institutions need a centralized notice board to broadcast time-sensitive communications (academic calendar changes, exam alerts, policy updates) to specific audiences. Currently there is no mechanism to push targeted announcements with acknowledgment tracking — critical for compliance-sensitive notices where the institution must prove recipients were informed.

## What Changes

- **New model `Aviso`**: Tenant-scoped notice with audience segmentation (alcance, rol_destino, materia_id, cohorte_id), visibility window (inicio_en/fin_en), severity levels, display ordering, and acknowledgment requirement flag
- **New model `AcknowledgmentAviso`**: Immutable confirmation record linking a user to an aviso they acknowledged
- **Full CRUD API** for avisos (`avisos:publicar` permission — COORDINADOR, ADMIN)
- **Public read endpoint** filtered by authenticated user's roles, materias, and cohortes — returns only visible avisos within their window
- **Acknowledgment endpoint** for users to confirm an aviso (`avisos:confirmar` permission — all authenticated users)
- **Migration `018_avisos.py`**: New tables, permission seeds for `avisos:publicar` and `avisos:confirmar`

## Capabilities

### New Capabilities
- `avisos-abm`: CRUD of avisos with audience configuration, visibility window, severity, ordering, active/inactive toggle, and acknowledgment requirement
- `avisos-visibility`: Filtered query that returns only avisos visible to the current user based on alcance, rol_destino, materia/cohorte associations, and current datetime within inicio_en/fin_en
- `avisos-acknowledgment`: Endpoint to confirm an aviso (requiere_ack), with counter query for acknowledgment status per aviso

### Modified Capabilities
- `rbac-permission-catalogue`: Add permissions `avisos:publicar` and `avisos:confirmar` to the seed data

## Impact

- **Models**: New `Aviso` and `AcknowledgmentAviso` in `backend/app/models/avisos.py`, registered in `models/__init__.py`
- **Schemas**: New request/response DTOs in `backend/app/schemas/avisos.py`
- **Router**: New `backend/app/routers/avisos.py` with CRUD + read + acknowledge endpoints
- **Service**: New `backend/app/services/avisos.py` with business logic for visibility filtering
- **Repository**: New `backend/app/repositories/avisos.py` extending TenantScopedRepository
- **Migration**: `018_avisos.py` — create tables, seed permissions
- **Tests**: New `backend/tests/avisos/` with coverage for CRUD, visibility filtering, acknowledgment
- **Permissions**: Seeds for `avisos:publicar` (COORDINADOR, ADMIN) and `avisos:confirmar` (all roles)
