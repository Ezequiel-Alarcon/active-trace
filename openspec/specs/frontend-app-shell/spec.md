# frontend-app-shell Specification

## Purpose
TBD - created by archiving change c-21-frontend-shell-y-auth. Update Purpose after archive.
## Requirements
### Requirement: The frontend is a Vite + React 18 + TypeScript SPA with feature-based structure

The system SHALL provide a `frontend/` project built with Vite, React 18, and TypeScript with `strict: true`. The source MUST be organized as `src/features/{name}/{components,hooks,services,types,pages}` plus a shared layer `src/shared/{services,components,hooks}`. The TypeScript configuration MUST forbid `any` (`noImplicitAny: true`) and the codebase MUST NOT use class components. An import alias `@/` MUST resolve to `src/`.

#### Scenario: The project builds and type-checks without `any`

- **WHEN** the TypeScript compiler runs over `frontend/src`
- **THEN** type-checking completes with no errors
- **AND** no source file declares or relies on an implicit `any` type
- **AND** the alias `@/shared/services/api` resolves to `frontend/src/shared/services/api`

#### Scenario: Auth feature follows the feature-based folder convention

- **WHEN** the `auth` feature is inspected
- **THEN** it exposes `components/`, `hooks/`, `services/`, `types/`, and `pages/` subfolders under `src/features/auth/`
- **AND** every React component file name is PascalCase and matches its exported component name

### Requirement: An authenticated layout wraps protected routes and hosts the permission-aware menu

The system SHALL provide an `AppLayout` component that renders a header, a navigation menu, and a content outlet for authenticated routes. Public routes (login, forgot, reset) MUST render outside `AppLayout`. The layout MUST consume the current session for the menu and MUST NOT contain business logic beyond layout and navigation.

#### Scenario: Authenticated routes render inside the layout

- **WHEN** an authenticated user navigates to a protected route
- **THEN** the route content renders inside `AppLayout` (header + menu + content outlet)

#### Scenario: Public auth routes render outside the layout

- **WHEN** an unauthenticated user navigates to `/login`, `/forgot`, or `/reset`
- **THEN** the page renders WITHOUT `AppLayout` (no authenticated header or menu)

### Requirement: The shell provides 403 and 404 pages

The system SHALL provide a `Forbidden403` page rendered when an authenticated user lacks the permission required by a route, and a `NotFound404` page rendered for unknown routes.

#### Scenario: Unknown route renders the 404 page

- **WHEN** a user navigates to a route that does not exist
- **THEN** the `NotFound404` page is rendered

#### Scenario: Forbidden page is shown for an authenticated user without the route permission

- **WHEN** an authenticated user without the required permission reaches a permission-guarded route
- **THEN** the `Forbidden403` page is rendered instead of the route content

#### Scenario: Sidebar muestra sección de Coordinación para roles con permisos

- **WHEN** un usuario autenticado tiene permisos de COORDINADOR o ADMIN
- **THEN** el sidebar SHALL mostrar una sección "Coordinación" con sub-ítems: Equipos, Avisos, Tareas, Monitor, Encuentros, Coloquios, Setup de Cuatrimestre
- **AND** cada sub-ítem SHALL filtrarse por permiso (fail-closed: sin permiso → no se muestra)

#### Scenario: Rutas de coordinación registradas en el router

- **WHEN** el enrutador se inicializa
- **THEN** SHALL existir rutas protegidas por permiso para:
  - /coordinacion/equipos (permiso equipos:asignar)
  - /coordinacion/avisos (permiso avisos:publicar)
  - /coordinacion/tareas (permiso tareas:ver)
  - /coordinacion/monitor (permiso analisis:ver)
  - /coordinacion/encuentros (permiso encuentros:ver)
  - /coordinacion/coloquios (permiso coloquios:ver)
  - /coordinacion/setup (permiso estructura:gestionar)
- **AND** cada ruta SHALL cargar su página mediante React.lazy

#### Scenario: Ruta /coordinacion redirige a equipos

- **WHEN** un usuario navega a /coordinacion
- **THEN** el sistema SHALL redirigir a /coordinacion/equipos

