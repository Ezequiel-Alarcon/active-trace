## Context

C-10 and C-11 were marked complete, but the current backend still breaks the central PROFESOR flow described in FL-02: select commission, import grades, then inspect atrasados, ranking, reportes and notas finales. The frontend delivered in C-22 consumes these routes with MSW fixtures, so it looks complete in isolation, but the real backend still returns empty hardcoded responses or fails before persistence.

Current backend state:

- `POST /api/calificaciones/import/confirm` declares `Depends(_get_import_service)` inside the function body. FastAPI does not resolve dependencies there, so confirm receives a `Depends` object and breaks at runtime.
- `GET /api/comisiones` is missing from `main_router.py`, while C-22 calls it to populate the commission workspace selector.
- `GET /api/analisis/atrasados` and `GET /api/analisis/ranking` return hardcoded empty responses from the router instead of service data.
- `GET /api/reportes/notas-finales` and `GET /api/reportes/materia/{materia_id}` call the service partially but discard the returned rows or names.
- `AnalisisRepository.get_alumnos_atrasados` builds a query and returns `[]`; `get_ranking` counts notes, not approved activities according to the configured threshold.

Important model reality: the implemented `Calificacion` model stores `usuario_id`, `materia_id`, optional `asignacion_id`, optional `version_padron_id`, and `nota` as JSON. Approval is derived with `derivar_aprobado(nota, umbral_pct, conjunto_aprobado)`, not stored. The design must use this implemented model, not the older conceptual shape with separate numeric/textual columns.

Governance is MEDIUM/HIGH because this touches tenant-scoped academic data and PII (`email_enc`). Implementation must stay within Routers -> Services -> Repositories -> Models, with identity and tenant coming only from the JWT/session.

## Goals / Non-Goals

**Goals:**

- Restore the real backend path for FL-02: commission listing -> import confirm -> analysis/reporting responses with persisted data.
- Add `GET /api/comisiones` using a derived commission view from existing tables, without creating schema.
- Replace router stubs with service calls and repository queries that are tenant-scoped and soft-delete aware.
- Compute approvals through the existing `derivar_aprobado` business rule and configured `UmbralMateria` values.
- Return response DTOs that match existing frontend types and backend Pydantic schemas with `extra='forbid'`.
- Cover each affected endpoint with API-level tests against a real test database, including empty and tenant-isolation cases.

**Non-Goals:**

- No frontend refactor in this change. Existing C-22 code keeps consuming the current contracts.
- No new database schema or Alembic migration. Commissions are derived from `VersionPadron`, `Materia`, and `Cohorte`.
- No redesign of PA-01 / full `InstanciaDictado`. This change documents a pragmatic mapping only.
- No hardening of unrelated C-11 monitor/export endpoints beyond preserving existing behavior.
- No external Moodle/N8N integration changes.

## Decisions

### 1. Represent commission as a derived `(materia_id, cohorte_id)` workspace

`GET /api/comisiones` will return commissions derived from active, non-deleted `VersionPadron` rows joined to `Materia` and `Cohorte`. The returned `id` will be a stable synthetic string built from both UUIDs, for example `<materia_id>:<cohorte_id>`, while `materia_id`, `materia_nombre`, `cohorte_id`, and `cohorte_nombre` remain explicit fields.

Why: the current data model has no `Comision` table. `VersionPadron` is the implemented entity that already binds `materia_id` and `cohorte_id`, and C-22 only needs a workspace selector plus the IDs to drive existing endpoints.

Alternative considered: create a real `comision` or `instancia_dictado` table. Rejected because proposal impact says no schema change, and PA-01 is still open for the broader academic-structure model.

Alternative considered: return `id = materia_id` to match current frontend comments. Rejected because it loses cohort identity and makes tenant data with the same materia across cohorts ambiguous. The explicit `materia_id` is the field consumers should pass to analysis routes that currently require only a materia.

### 2. Keep permissions explicit and fail-closed at each endpoint

`GET /api/comisiones` will require an explicit permission suitable for reading the academic workspace, preferably `analisis:ver` unless the existing RBAC matrix already has a more precise commission/list permission. Existing analysis endpoints keep `analisis:ver`; report endpoints keep `reportes:ver`; import confirm keeps `calificaciones:importar`.

Why: permissions are endpoint contracts in this repo. Missing or ambiguous permission must deny by default.

Alternative considered: rely on authentication only for commission listing. Rejected because it violates RBAC fail-closed and would expose academic structure to any logged-in user.

### 3. Resolve identity and tenant once, pass tenant to services/repositories

Routers will continue resolving `current_user` and `AsyncSession` through FastAPI dependencies. Services are constructed with `current_user.tenant_id`; repositories apply `tenant_id` and `deleted_at IS NULL` in every query. No endpoint will accept tenant or user identity from query/body/header.

Why: this is the project's core multi-tenancy invariant and must be tested directly with cross-tenant fixtures.

Alternative considered: accepting `tenant_id` for admin-style filtering. Rejected for this change because it would violate the session-derived identity rule and is not required by C-22.

### 4. Fix `import_confirm` by moving the import-service dependency to endpoint parameters

`import_confirm` will mirror `import_preview`: receive `svc_tuple: tuple[ImportService, dict[str, UUID], set[UUID], set[UUID]] = Depends(_get_import_service)` as a function parameter and then call `svc.confirm_import(...)`.

Why: this is the smallest correct fix and preserves the existing `ImportService` contract.

Alternative considered: create a new dependency that returns only `ImportService`. Acceptable later, but not necessary for this bug fix.

### 5. Compute analysis rows in repositories, derive business semantics in services

Repositories will perform SQL joins and aggregation only: load active padron entries, grades, thresholds, materia/cohorte names, and user/entry identity fields under tenant scope. Services will map rows into response-shaped dictionaries, derive `estado`, `cantidad_aprobadas`, `tasa_aprobacion`, and approval booleans using `derivar_aprobado`.

Why: SQL belongs in repositories, while approval semantics are business logic and must be consistently reused from C-10.

Alternative considered: compute approval purely in SQL. Rejected because `nota` is JSON and text/list approval depends on `derivar_aprobado`; duplicating that logic in SQL risks semantic drift.

### 6. Use active padron as the expected roster for atrasados/reportes

For atrasados and materia reportes, the expected student set comes from active `VersionPadron` entries for the selected `materia_id` and optional `cohorte_id`. A student is atrasado when at least one expected activity has no grade or has a grade that fails the configured threshold. If `VersionPadron.actividades` is empty, the endpoint returns an empty analysis list rather than inventing expected activities.

Why: C-09 introduced active padron versions and activities; using them avoids guessing from incomplete grade rows and lets missing activities be detected.

Alternative considered: infer expected activities only from existing `Calificacion` rows. Rejected because missing activities would be invisible, which is exactly one of the atrasados definitions.

### 7. Decrypt PII only at response mapping boundaries

Emails returned in analysis/report DTOs will be decrypted from `EntradaPadron.email_enc` or `Usuario.email_enc` using existing helpers (`decrypt_entrada_email` or `decrypt_usuario_fields`) only when constructing the response. Decrypted emails must not be logged or stored in intermediate persisted fields.

Why: emails are PII and the project requires AES-256 at rest. The frontend contract currently displays email, so plaintext exposure is limited to authorized API responses.

Alternative considered: omit email from responses. Rejected because existing schemas/frontend fixtures include `email` and changing that would be a frontend contract break outside this change.

### 8. API-level TDD catches the original failure mode

Tests for this change should call the FastAPI routes with authenticated users and a real test DB, not isolated service methods and not DB mocks. Each route needs at least one positive seeded-data test, one empty-state test where applicable, and one tenant-isolation or authorization test.

Why: the defect survived because routers returned hardcoded data while service-level behavior was assumed to be enough. The apply phase must test the actual HTTP contract.

Alternative considered: unit-test repositories with mocked sessions. Rejected by project rule and because it would not catch dependency-injection/router wiring bugs.

## Risks / Trade-offs

- [Risk] `comision.id` as `<materia_id>:<cohorte_id>` may require small frontend follow-up because some C-22 components still pass `comisionId` as `materia_id`. -> Mitigation: keep explicit `materia_id`/`cohorte_id` in the response and document that consumers must use `materia_id` for existing analysis endpoints; avoid changing frontend in this backend change unless a test proves the current UI cannot use the mapping.
- [Risk] Approval derivation in Python can require loading more rows than a pure aggregate SQL query. -> Mitigation: keep limits bounded, query only tenant/materia/cohorte rows, and aggregate in memory after narrowing the dataset.
- [Risk] Existing imports may not populate `VersionPadron.actividades`, making missing-activity detection incomplete. -> Mitigation: return empty/known-grade based results deterministically and add a `# TODO: (REVIEW)` during implementation only if the source data cannot represent expected activities.
- [Risk] Decryption errors could turn a whole report into 500. -> Mitigation: use existing decrypt helpers consistently and let tests seed encrypted PII through repositories/helpers instead of plaintext shortcuts.
- [Risk] Existing RBAC matrix may not include the selected permission for `/api/comisiones`. -> Mitigation: use an existing explicit read permission if available; otherwise add the smallest permission mapping change with tests for 401/403.
- [Risk] The current `AnalisisRepository` is already near several responsibilities. -> Mitigation: add focused methods for each response instead of mixing router/service formatting into SQL code; split only if file size approaches the 500 LOC rule.

## Migration Plan

No database migration is planned.

Implementation order:

1. Add failing API tests for the currently broken routes and missing `/api/comisiones` route.
2. Add `ComisionRead` schema, repository/service/router for commission listing, and mount the router in `main_router.py`.
3. Fix `import_confirm` dependency injection and prove persistence through endpoint tests.
4. Replace analysis/report router stubs with service calls and implement repository/service logic behind them.
5. Run targeted backend tests and lightweight OpenSpec validation.

Rollback strategy: revert this change's backend files and tests. Because no schema is changed, rollback is code-only.

## Open Questions

- PA-01 remains open: this change does not settle whether the final domain concept should be `Materia`, `InstanciaDictado`, or a dedicated `Comision` table. It only uses `(materia_id, cohorte_id)` as the current operational workspace.
- Should `/api/comisiones` include only active padron versions, or also active `Asignacion` contexts with no imported padron yet? For this change, use active padron versions because they are sufficient for import/analysis and avoid exposing empty academic setup.
- Should ranking/report endpoints accept `cohorte_id` now that commissions include it? Existing frontend/backend contracts mainly use `materia_id`; adding optional `cohorte_id` is safe if tests prove cross-cohort ambiguity, but it is not required by the current spec.
