# Tasks: C-21 — Frontend Shell y Auth

> **Strict TDD**: para cada tarea de lógica/componente, escribir primero el test que falla (RED), luego el código mínimo (GREEN), triangular con un 2º caso, y refactorizar. Tests con MSW; nunca mockear el cliente Axios que se está probando.
> **Pre-requisito de las tareas del guard (sección 7)**: cerrar OQ-1 (endpoint `GET /api/auth/session` con permisos efectivos). Ver design.md.

## 1. Scaffolding del proyecto

- [x] 1.1 Crear `frontend/` con Vite (template `react-ts`): `package.json`, `vite.config.ts`, `tsconfig.json` (`strict: true`, `noImplicitAny: true`), `index.html`, `src/main.tsx`, `src/App.tsx`.
- [x] 1.2 Configurar el alias `@/` → `src/` en `vite.config.ts` y `tsconfig.json` (paths).
- [x] 1.3 Instalar y configurar Tailwind CSS (`tailwind.config.js`, `postcss.config.js`, directivas en `src/index.css`).
- [x] 1.4 Instalar dependencias runtime: `axios`, `@tanstack/react-query`, `react-router-dom`, `react-hook-form`, `zod`, `@hookform/resolvers`.
- [x] 1.5 Instalar y configurar testing: `vitest`, `@testing-library/react`, `@testing-library/user-event`, `jsdom`, `msw`. Crear `vitest.config.ts` y `src/test/setup.ts`.
- [x] 1.6 Crear el setup base de MSW (`src/test/server.ts` con `setupServer`) y los handlers iniciales vacíos.
- [x] 1.7 Crear la estructura de carpetas: `src/features/auth/{components,hooks,services,types,pages}` y `src/shared/{services,components,hooks}` (con un `.gitkeep` o archivo índice según convenga).

## 2. Token store y tipos de sesión

- [x] 2.1 (RED→GREEN) `src/shared/services/tokenStore.ts`: singleton en memoria con `get/set/clear` del access token. Test: set→get devuelve el token; clear→get devuelve null.
- [x] 2.2 `src/features/auth/types/session.ts`: tipos `SessionUser`, `Session` (`{user, roles, permissions: string[]}`), `LoginRequest`, `AuthErrorCode` (union de los `code` de C-03). Sin `any`.

## 3. Cliente HTTP centralizado (interceptor de request)

- [x] 3.1 (RED→GREEN) `src/shared/services/api.ts`: instancia Axios con `baseURL` desde env. Interceptor de request que adjunta `Authorization: Bearer <token>` si hay token en el store. Test (MSW): con token en el store, el request lleva el header.
- [x] 3.2 (TRIANGULATE) Test: sin token, el request no lleva header; para `login/forgot/reset` no se adjunta token aunque exista uno viejo.

## 4. Refresh transparente (interceptor de response)

- [x] 4.1 (RED→GREEN) Interceptor de response: ante `401` (no en `/auth/refresh` ni `/auth/login`), llama `POST /api/auth/refresh`, actualiza el token y reintenta la petición original una vez. Test (MSW): 1er request → 401, refresh → 200, reintento → 200; el caller recibe el 200, nunca el 401.
- [x] 4.2 (TRIANGULATE) Single-flight: 3 requests concurrentes con 401 disparan EXACTAMENTE un `POST /api/auth/refresh`; los 3 se reintentan con el nuevo token. Test con contador de llamadas a refresh en MSW.
- [x] 4.3 (RED→GREEN) Refresh fallido (`401` en `/auth/refresh`): limpia el token store, rechaza la cola y dispara navegación a `/login`. Test: refresh → 401 ⇒ token store vacío + callback de logout invocado.
- [x] 4.4 (RED→GREEN) `403`: se propaga como error de permiso, sin refresh ni reintento. Test: request → 403 ⇒ no se llama refresh, no se reintenta, el caller recibe el error.

## 5. Estado de sesión (TanStack Query + AuthProvider)

- [x] 5.1 Configurar `QueryClient` y `QueryClientProvider` en `App.tsx`.
- [x] 5.2 (RED→GREEN) `src/features/auth/hooks/useSession.ts`: query key `['session']` que bootstrappea desde el endpoint de sesión. Test (MSW): devuelve `{user, permissions}` del server.
- [x] 5.3 (RED→GREEN) `src/features/auth/components/AuthProvider.tsx` + `useAuth`: expone `session`, `isAuthenticated`, `hasPermission(perm)`, `login`, `logout`. Test: `hasPermission` true/false según el set de permisos (happy + edge vacío).

## 6. Feature auth — pantallas y hooks

- [x] 6.1 (RED→GREEN) `src/features/auth/services/authApi.ts`: funciones `login`, `verify2fa`, `forgot`, `reset`, `logout` que llaman a C-03 vía el cliente centralizado. Tests (MSW) por función: shape de request y mapeo de respuesta/`code`.
- [x] 6.2 (RED→GREEN) `LoginForm.tsx` + `useLogin` (RHF + Zod: `tenant_codigo`, `email`, `password`). Test: render del form; submit válido → llama login y guarda token; validación bloquea submit con email inválido.
- [x] 6.3 (TRIANGULATE) Test: `AUTH_INVALID_CREDENTIALS` → mensaje genérico; el mensaje no revela qué campo falló.
- [x] 6.4 (RED→GREEN) Paso 2FA: ante `AUTH_2FA_REQUIRED`, transicionar al `TwoFactorForm.tsx` (código de 6 dígitos). Test: 401 `AUTH_2FA_REQUIRED` → render del step; código válido → sesión; `AUTH_2FA_INVALID` → permanece con mensaje genérico.
- [x] 6.5 (RED→GREEN) `ForgotPasswordForm.tsx` + `useForgot`: siempre mensaje neutro (no enumeración). Test: 200 → mensaje neutro idéntico exista o no el email.
- [x] 6.6 (RED→GREEN) `ResetPasswordForm.tsx` + `useReset`: lee el token, valida nueva password con Zod (min length), llama reset. Test: 200 → éxito + ruta a login; `AUTH_RESET_EXPIRED/INVALID` → mensaje recuperable con link a forgot.
- [x] 6.7 (RED→GREEN) `useLogout`: llama logout, limpia token+sesión, navega a `/login`. Test: 204 → limpia y navega; error backend → igual limpia local y navega.

## 7. Guard de rutas y menú (depende de OQ-1)

- [x] 7.1 Confirmar/cerrar OQ-1: contrato del endpoint de sesión con `permissions[]`. Si falta, registrar TODO y/o coordinar el mini-cambio backend antes de continuar esta sección.
- [x] 7.2 (RED→GREEN) `src/shared/components/RequireAuth.tsx`: sin sesión → `Navigate` a `/login` preservando `from`; bootstrap en curso → loading. Tests: sin sesión redirige; bootstrap-in-flight muestra loading sin redirigir.
- [x] 7.3 (RED→GREEN) `src/shared/components/RequirePermission.tsx`: con permiso → contenido; sin permiso → `Forbidden403`; set vacío → bloquea todo (fail-closed). Tests: los 3 casos.
- [x] 7.4 (RED→GREEN) Menú permission-aware en `AppLayout`: usa `hasPermission` para filtrar ítems. Test: ítem con permiso se renderiza, ítem sin permiso no.

## 8. Shell, layout y ruteo

- [x] 8.1 (RED→GREEN) `src/shared/components/AppLayout.tsx`: header + menú + `Outlet`. Test: rutas autenticadas renderizan dentro del layout; rutas públicas (login/forgot/reset) fuera.
- [x] 8.2 (RED→GREEN) Páginas `Forbidden403.tsx` y `NotFound404.tsx`. Test: ruta inexistente → 404; sin permiso → 403.
- [x] 8.3 Definir el árbol de rutas (`react-router-dom`): públicas (`/login`, `/forgot`, `/reset`) y protegidas bajo `RequireAuth` + `AppLayout`, con una ruta protegida de ejemplo guardada por `RequirePermission`. Wire del `AuthProvider` y los providers en `App.tsx`.
- [x] 8.4 Bootstrap al arranque: si hay refresh disponible, intentar bootstrap de sesión; si falla → `/login`. Test: arranque con sesión válida entra; sin sesión va a login.

## 9. Cierre

- [x] 9.1 Verificar cobertura de los flujos críticos (login render, auth con mock, 2FA, guard sin sesión, guard sin permiso, refresh transparente single-flight) — ≥80% líneas en `features/auth` y `shared/services`.
- [x] 9.2 Pasar el type-check (`tsc --noEmit`) y el linter sin `any` ni class components. Marcar cualquier pendiente con `# TODO: (PREFIJO)` / `// TODO: (PREFIJO)` según corresponda.
- [x] 9.3 (Opcional, solo si el usuario lo pide) agregar servicio `frontend` a docker-compose dev. NO buildear sin pedido explícito.
