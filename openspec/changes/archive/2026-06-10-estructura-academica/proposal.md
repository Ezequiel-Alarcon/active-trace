## Why

El sistema necesita un catálogo de estructura académica (carreras, cohortes y materias) para que ADMIN pueda configurar la oferta académica del tenant. Sin esto, los cambios posteriores de importación de calificaciones, detección de atrasos y comunicación masiva no tienen sobre qué entidades operar. Es la base del dominio académico.

## What Changes

- Nuevos modelos ORM: `Carrera`, `Cohorte`, `Materia` — todos con `TenantScopedMixin` (soft delete, tenant scoping, UUID PK).
- Migración Alembic `005_estructura_academica` que crea las tres tablas con índices de unicidad por tenant y FK adecuadas.
- Schemas Pydantic v2 con `extra='forbid'` para request/response de cada entidad.
- Repositorio `EstructuraRepository` que extiende `TenantScopedRepository` con validaciones de negocio (unicidad por código, carrera activa para cohortes).
- Servicio `EstructuraService` con la lógica de ABM y reglas de negocio (RN-E1, RN-E2, RN-E3).
- Router `/api/admin/carreras`, `/api/admin/cohortes`, `/api/admin/materias` protegido con `require_permission("estructura:gestionar")`.
- Tests: CRUD, unicidad por tenant, aislamiento multi-tenant, validación de carrera inactiva al crear cohorte.

## Capabilities

### New Capabilities

- `estructura-academica-carreras`: ABM de carreras (alta, edición, cambio de estado activa/inactiva). Unicidad `(tenant_id, codigo)`. Carrera inactiva no admite cohortes abiertas.
- `estructura-academica-cohortes`: ABM de cohortes (alta, edición, cambio de estado). Unicidad `(tenant_id, carrera_id, nombre)`. Validación de carrera activa al crear. FK a Carrera con ON DELETE RESTRICT.
- `estructura-academica-materias`: ABM del catálogo de materias (alta, edición, cambio de estado activa/inactiva). Unicidad `(tenant_id, codigo)`. ADR-006: Materia es el catálogo único; la instancia de dictado (por carrera×cohorte) se crea en un change futuro.

### Modified Capabilities

_Ninguna. Este change introduce capacidades nuevas sin alterar specs existentes._

## Impact

- **Modelos**: tres nuevos archivos en `app/models/` (`carrera.py`, `cohorte.py`, `materia.py`) + registro en `app/models/__init__.py`.
- **Migración**: `alembic/versions/005_estructura_academica.py` (down revision: `004_rbac`).
- **Schemas**: `app/schemas/estructura.py` con Pydantic DTOs para request/response.
- **Repositorios**: `app/repositories/estructura.py` con validaciones de negocio sobre `TenantScopedRepository`.
- **Servicios**: `app/services/estructura.py` con lógica de ABM y reglas.
- **Router**: `app/routers/estructura.py` montado en `/api/admin` con guard `estructura:gestionar`.
- **Tests**: `tests/estructura/test_carreras.py`, `test_cohortes.py`, `test_materias.py`.
- **RBAC**: el permiso `estructura:gestionar` ya existe (seed de migración 004); ADMIN lo posee. Sin cambios en migraciones ni seeds de RBAC.
