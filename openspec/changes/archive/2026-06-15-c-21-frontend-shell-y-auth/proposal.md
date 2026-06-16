# Proposal: C-21 — Frontend Shell y Auth

## Why

activia-trace tiene todo su backend de autenticación (C-03) y autorización RBAC (C-04) en producción, pero no existe ninguna interfaz de usuario que lo consuma. Sin un shell frontend con auth, las features de las fases siguientes (C-22 académico-docente, C-23 coordinación, C-24 finanzas) no tienen dónde montarse. C-21 construye el esqueleto SPA común: scaffolding, cliente HTTP con refresh transparente, las pantallas del flujo de autenticación (FL-01) y la navegación adaptada a los permisos de la sesión. Es la base sobre la que se apoya toda la FASE 5.

## What Changes

- **Scaffolding del proyecto frontend** (`frontend/`): React 18 + TypeScript + Vite, estructura feature-based (`features/{name}/{components,hooks,services,types,pages}` + `shared/`), Tailwind CSS, TanStack Query, React Hook Form + Zod, Axios. Sin `any`, sin class components, componentes <200 LOC.
- **Cliente HTTP centralizado** (`shared/services/api.ts`): instancia Axios única con interceptor de request (adjunta el access token) y de response. El interceptor de response detecta `401`, dispara un **refresh transparente** del par de tokens contra `POST /api/auth/refresh` (con cola de peticiones en vuelo y deduplicación del refresh concurrente), y reintenta la petición original. Si el refresh falla → limpia la sesión y redirige a login. Maneja `403` propagando un error de permiso (no reintenta).
- **Almacenamiento de sesión en memoria**: el access token y el estado de sesión viven en memoria (no en `localStorage` para el access token); el refresh token se maneja según el contrato de C-03 (header `Authorization: Bearer`). La identidad y los permisos NUNCA se derivan de parámetros de URL/body — solo de la sesión bootstrappeada server-side.
- **Feature `auth`**: pantallas de **login** (email + password + `tenant_codigo`), **2FA** (TOTP cuando el login responde `AUTH_2FA_REQUIRED`), **recuperación de contraseña** (forgot → email; reset con token) y **logout**. Todas consumen los endpoints de C-03 vía hooks de `services/` (TanStack Query mutations).
- **Bootstrap de sesión**: tras login exitoso, el frontend obtiene el usuario actual y sus **permisos efectivos** desde un endpoint de sesión server-side (ver Impact / supuesto SUP-01). Esos permisos alimentan el guard y el menú.
- **Guard de rutas por permiso** (`shared/components/RequirePermission`, `RequireAuth`): un componente/route-wrapper que redirige a login si no hay sesión, y a una página `403` si la sesión no tiene el permiso `modulo:accion` requerido por la ruta. **Fail-closed**: sin permiso explícito → bloqueado.
- **Layout y menú adaptados a permisos**: el shell (header, sidebar/menú, área de contenido) renderiza solo los ítems de navegación para los que la sesión tiene permiso. Las rutas sin sesión (login, forgot, reset) viven fuera del layout autenticado.
- **Tests** (Vitest + Testing Library): render de login, flujo de auth con backend mockeado (MSW), 2FA, el guard redirige sin sesión y bloquea sin permiso, y el **refresh transparente** reintenta tras un `401`.

## Capabilities

### New Capabilities
- `frontend-app-shell`: Scaffolding del proyecto (Vite + React 18 + TS), estructura feature-based, configuración de Tailwind/TanStack Query/RHF+Zod, layout autenticado y ruteo base con páginas `403`/`404`.
- `frontend-http-client`: Cliente Axios centralizado con interceptores de auth, refresh transparente de tokens (con deduplicación y cola de reintento) y manejo uniforme de `401`/`403`.
- `frontend-auth-flow`: Pantallas y hooks del flujo de autenticación — login, 2FA (TOTP), forgot/reset de contraseña, logout y bootstrap de la sesión.
- `frontend-route-guard`: Guard de autenticación y autorización por permiso `modulo:accion` (fail-closed) y menú/navegación adaptado a los permisos efectivos de la sesión.

### Modified Capabilities
- (Ninguna. C-21 no modifica requisitos de specs backend existentes; solo los consume.)

## Impact

| Área | Impacto |
|------|--------|
| **Nuevo proyecto** | `frontend/` con su propio `package.json`, `vite.config.ts`, `tsconfig.json`, `tailwind.config.js`, setup de Vitest + MSW. |
| **Estructura** | `frontend/src/features/auth/{components,hooks,services,types,pages}` + `frontend/src/shared/{services,components,hooks}`. |
| **APIs consumidas (C-03)** | `POST /api/auth/login`, `POST /api/auth/refresh`, `POST /api/auth/logout`, `POST /api/auth/forgot`, `POST /api/auth/reset`, `POST /api/auth/2fa/verify`. |
| **APIs consumidas (C-04)** | Resolución de permisos server-side; el menú/guard lee los permisos efectivos del bootstrap de sesión. |
| **Sin cambios backend** | C-21 NO crea ni modifica endpoints; es puramente frontend. |
| **DevOps** | Servicio `frontend` en docker-compose (dev) queda como TODO de C-21 si se requiere; el deploy productivo lo cubre infra (C-01/Easypanel). |

> **SUP-01 (supuesto a confirmar antes de apply)**: el guard y el menú necesitan los **permisos efectivos** de la sesión. C-03/C-04 resuelven permisos server-side pero **no exponen un endpoint que los devuelva al cliente** (no hay `GET /api/auth/me` en las specs revisadas). C-21 asume un endpoint de bootstrap de sesión `GET /api/auth/session` que devuelve `{user: {id, email, roles}, permissions: ["modulo:accion", ...]}`. Si ese endpoint no existe, debe agregarse como un pequeño cambio backend (C-04.x) o incluirse en el scope de apply de C-21 con su propio spec/tasks de backend. La identidad y los permisos SIEMPRE salen de ese bootstrap server-side, nunca de datos de la petición del cliente. **Resolver antes de implementar el guard.**
