## 1. Failing API Tests

- [x] 1.1 Add a failing backend API test for `GET /api/comisiones` that seeds two tenants with active `VersionPadron`, `Materia`, and `Cohorte` rows and asserts only the authenticated tenant's commissions are returned.
- [x] 1.2 Add a failing backend API test for `GET /api/comisiones` with no active commissions that asserts `200` and an empty list.
- [x] 1.3 Add a failing backend API test for `POST /api/calificaciones/import/confirm` proving the endpoint resolves `_get_import_service` through FastAPI dependency injection and persists valid preview rows.
- [x] 1.4 Add failing backend API tests for `GET /api/analisis/atrasados` that seed an active padron, thresholds, and grades, then assert delayed students are returned instead of `alumnos=[]`.
- [x] 1.5 Add failing backend API tests for `GET /api/analisis/ranking` that assert only approved activities counted by `derivar_aprobado` contribute to `cantidad_aprobadas` and ordering is descending.
- [x] 1.6 Add failing backend API tests for `GET /api/reportes/notas-finales` and `GET /api/reportes/materia/{materia_id}` proving routers return service/repository data instead of discarding rows.

## 2. Commission Listing

- [x] 2.1 Add a Pydantic response schema for a commission item with `id`, `materia_id`, `materia_nombre`, `cohorte_id`, and `cohorte_nombre`, using `ConfigDict(extra='forbid')`.
- [x] 2.2 Implement a tenant-scoped repository query that derives commissions from active, non-deleted `VersionPadron` rows joined to non-deleted `Materia` and `Cohorte` rows.
- [x] 2.3 Implement a service method that maps repository rows to the frontend contract and builds a stable synthetic `id` from `materia_id` and `cohorte_id`.
- [x] 2.4 Add a `GET /api/comisiones` router endpoint that resolves identity from the session, requires an explicit read permission, and contains no business logic.
- [x] 2.5 Mount the comisiones router in `backend/app/api/v1/main_router.py` and remove or update the obsolete TODO at the missing-router location.

## 3. Import Confirm Fix

- [x] 3.1 Move the `_get_import_service` dependency in `import_confirm` from the function body into the endpoint parameter list, mirroring `import_preview`.
- [x] 3.2 Keep `calificaciones:importar` authorization and current `ImportService.confirm_import` behavior unchanged.
- [x] 3.3 Verify the endpoint test asserts persisted, skipped, and failed counts from a real database path, not a mocked DB/session.

## 4. Analysis And Report Implementation

- [x] 4.1 Implement `AnalisisRepository.get_alumnos_atrasados` so it executes tenant-scoped queries over active padron entries, grades, thresholds, materia/cohorte names, and soft-delete filters.
- [x] 4.2 Add or update `AnalisisService.get_alumnos_atrasados` to derive atrasado status with `derivar_aprobado`, decrypt response emails only at response mapping time, and return `total`, `limit`, `offset`, and `alumnos` data.
- [x] 4.3 Update `GET /api/analisis/atrasados` to call the service result and stop returning the hardcoded empty response.
- [x] 4.4 Correct ranking logic so `cantidad_aprobadas` counts only grades approved by `derivar_aprobado`, `cantidad_totales` counts attempted/expected activities consistently, `nota_promedio` averages numeric notes only, and positions are assigned after descending sort.
- [x] 4.5 Update `GET /api/analisis/ranking` to return real `materia_nombre` and ranking rows from the service.
- [x] 4.6 Implement report-by-materia data mapping with real `materia_nombre`, `cohorte_id`, `cohorte_nombre`, `total_alumnos`, and `alumnos[].actividades`.
- [x] 4.7 Implement notas-finales mapping with real `materia_nombre`, `total_alumnos`, `aprobados`, `tasa_aprobacion`, and `nota_promedio_global`, preserving pagination response fields.
- [x] 4.8 Remove or replace stale `# TODO: (FIX)` markers for defects fixed by this change; keep any newly discovered limitation as a standardized `# TODO: (REVIEW|FIX|TEST)` at the exact source location.

## 5. Security, Tenancy, And RBAC Verification

- [x] 5.1 Assert all new and modified repository queries filter by `tenant_id` and `deleted_at IS NULL` for every tenant-scoped table involved.
- [x] 5.2 Assert no endpoint accepts `tenant_id` or user identity from query/body/header for these flows.
- [x] 5.3 Add or update authorization tests for unauthenticated `401` and unauthorized `403` behavior on `/api/comisiones` and at least one modified analysis/report endpoint.
- [x] 5.4 Verify decrypted emails are returned only in authorized API responses and are never logged or persisted in plaintext during this flow.

## 6. Validation

- [x] 6.1 Run targeted backend tests for calificaciones import confirm, comisiones listing, and analysis/report endpoints using the project's pytest setup.
- [x] 6.2 Run lint/format checks required by backend conventions, without running build/compile/bundle commands.
- [x] 6.3 Run `openspec status --change "c-26-completar-analisis-comisiones-import" --json` and confirm proposal, specs, design, and tasks are done before apply.
