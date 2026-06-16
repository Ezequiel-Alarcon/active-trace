# Design: C-21 — Frontend Shell y Auth

## Context

El backend de auth (C-03) y RBAC (C-04) está completo y archivado. C-03 expone `POST /api/auth/{login,refresh,logout,forgot,reset,2fa/verify,2fa/enroll}` con access token JWT de 15 min, refresh token con rotación DB-backed (un refresh usado se invalida; el reuse invalida toda la cadena), y errores con `code` semánticos (`AUTH_2FA_REQUIRED`, `AUTH_INVALID_CREDENTIALS`, `AUTH_TOKEN_EXPIRED`, `AUTH_TOKEN_REVOKED`, etc.). C-04 resuelve permisos efectivos server-side por request (unión de permisos de roles, scoped al tenant, fail-closed).

C-21 es el primer trabajo de frontend del proyecto: NO existe `frontend/` todavía. Este change crea el proyecto desde cero y el flujo de autenticación end-to-end (FL-01), dejando el shell listo para que C-22/23/24 monten sus features.

**Restricciones duras del proyecto** (de CLAUDE.md / docs/ARQUITECTURA.md):
- React 18 + TypeScript, sin `any`, sin class components, componentes <200 LOC.
- Estructura `features/{name}/{components,hooks,services,types,pages}` + `shared/`.
- Todo fetch pasa por hooks de `services/` (TanStack Query). Axios centralizado en `@/shared/services/api`.
- Tailwind (sin CSS modules, sin inline salvo valores dinámicos). RHF + Zod para forms.
- PascalCase: nombre del componente = nombre del archivo (`LoginForm.tsx`).
- Identidad/permisos SIEMPRE desde la sesión server-side, JAMÁS desde URL/body.
- Strict TDD: test que falla → código mínimo → triangulación → refactor.

**Gap detectado**: C-03/C-04 no exponen un endpoint que devuelva al cliente el usuario actual + sus permisos efectivos. El menú y el guard lo necesitan (ver SUP-01 en proposal). Este design asume `GET /api/auth/session`; ver Open Questions.

## Goals / Non-Goals

**Goals:**
- Scaffolding frontend reproducible y tipado, con la estructura feature-based del proyecto.
- Cliente HTTP único con refresh transparente robusto: un solo refresh ante N peticiones concurrentes que reciben `401`, con reintento de las originales.
- Flujo de auth completo consumiendo C-03: login, 2FA, forgot/reset, logout.
- Guard fail-closed por permiso `modulo:accion` + menú adaptado a permisos.
- Cobertura de tests sobre los flujos críticos (login render, auth con mock, 2FA, guard, refresh transparente).

**Non-Goals:**
- Features de negocio (atrasados, comunicación, liquidaciones, etc.) → C-22/23/24.
- Enrollment de 2FA con UX completa (QR setup wizard) → solo se cubre el `2fa/verify` en el flujo de login; el enroll puede quedar mínimo o como TODO.
- Impersonación UI → fuera de scope.
- Diseño visual final / design system completo → solo lo mínimo para que el shell funcione (Tailwind base).
- Cambios backend → C-21 es frontend-only; el endpoint de bootstrap de sesión, si falta, se resuelve aparte (ver Open Questions).

## Decisions

### D1 — Vite + React 18 + TypeScript, proyecto en `frontend/`
El stack está fijado por el proyecto. Vite por HMR y build rápido. `tsconfig` con `strict: true` y `noImplicitAny` para hacer cumplir "sin `any`". Alias `@/` → `src/` para imports limpios (`@/shared/services/api`).
**Alternativa descartada**: CRA (deprecado), Next.js (SSR innecesario para una SPA autenticada detrás de login).

### D2 — Access token en memoria, no en localStorage
El access token se guarda en un módulo singleton en memoria (`shared/services/tokenStore.ts`), no en `localStorage`/`sessionStorage`, para reducir superficie de XSS. El refresh se presenta al backend como `Authorization: Bearer <refresh>` según el contrato de C-03. Al recargar la página, si hay refresh disponible se intenta un bootstrap; si no, se va a login.
**Trade-off**: recargar pierde el access token en memoria → se resuelve con un refresh al arranque. Aceptable.
**Alternativa descartada**: persistir access token en localStorage → mayor superficie XSS, rechazado por la regla de seguridad del proyecto.

### D3 — Refresh transparente con deduplicación (single-flight)
El interceptor de response de Axios:
1. Ante `401` con `code` que indique token expirado/inválido y la petición no es ella misma un `/auth/refresh` ni `/auth/login`: marca la petición como "a reintentar".
2. Si **no hay** un refresh en vuelo → inicia uno (`POST /api/auth/refresh`) y guarda la `Promise` en una variable de módulo (single-flight). Si **ya hay** uno → espera esa misma `Promise`.
3. Cuando el refresh resuelve → actualiza el token en memoria y **reintenta** todas las peticiones encoladas con el nuevo token.
4. Si el refresh falla (`401 AUTH_TOKEN_REVOKED`/`EXPIRED`) → limpia la sesión, rechaza las encoladas y dispara navegación a `/login`.
**Por qué single-flight**: sin él, N peticiones con `401` dispararían N refresh concurrentes; como el refresh rota y un refresh usado invalida la cadena (C-03), el 2º refresh fallaría con `AUTH_TOKEN_REVOKED` y mataría la sesión. La deduplicación es **obligatoria**, no opcional.
**Alternativa descartada**: refrescar proactivamente por timer antes de expirar → más complejo, no cubre relojes desincronizados; el reactivo por `401` es más simple y robusto.

### D4 — Estado de sesión con TanStack Query + Context delgado
El usuario actual + permisos viven en una query (`useSession`) cacheada por TanStack Query (key `['session']`), bootstrappeada tras login o al arranque. Un `AuthProvider` (Context) expone `session`, `login`, `logout`, `isAuthenticated` y un helper `hasPermission(perm)`. Los hooks de auth son mutations que invalidan/setean la query de sesión.
**Por qué no Redux/Zustand**: TanStack Query ya es el server-state oficial; la sesión es server-state. Un Context delgado evita prop drilling sin agregar otra librería de estado.

### D5 — Guard fail-closed con dos niveles
- `RequireAuth`: wrapper de ruta. Si `!isAuthenticated` → `<Navigate to="/login" replace state={{from}}/>`. Mientras bootstrappea → muestra loading.
- `RequirePermission perm="modulo:accion"`: anida dentro de `RequireAuth`. Si la sesión no incluye `perm` → render de `<Forbidden403/>`. Sin permiso explícito → bloqueado (fail-closed).
- El menú usa el mismo `hasPermission` para filtrar ítems: un ítem sin permiso no se renderiza (defensa en profundidad junto al guard de ruta).
**Decisión clave**: la fuente de verdad de permisos es el bootstrap server-side; el frontend NUNCA decide permisos por sí mismo ni los infiere de la URL. El guard es UX/defensa; el backend sigue autorizando cada request (fail-closed real).

### D6 — Mapeo de `code` de error de C-03 a UX
El feature `auth` traduce los `code` del backend a estados de UI sin inventar lógica:
- `AUTH_2FA_REQUIRED` → transición a la pantalla/step de 2FA (no es un error visible, es un paso).
- `AUTH_2FA_INVALID` / `AUTH_INVALID_CREDENTIALS` → mensaje genérico "credenciales inválidas" (no filtrar qué falló).
- `forgot`/`reset` → siempre mensaje neutro de "si el email existe, te enviamos instrucciones" (respeta la no-enumeración del backend).
- `AUTH_RESET_EXPIRED`/`AUTH_RESET_INVALID` → "el enlace expiró o ya fue usado, solicitá uno nuevo".

### D7 — Testing: Vitest + Testing Library + MSW
Vitest (nativo de Vite) como runner; React Testing Library para render; **MSW** para mockear los endpoints de C-03 a nivel de red (no se mockea Axios ni se mockea fetch a mano). Esto permite testear el interceptor de refresh de verdad: MSW responde `401` la primera vez, `200` al refresh, y se verifica el reintento.
**Por qué MSW y no jest.mock de axios**: testear el interceptor requiere que la capa de red real responda; mockear axios saltearía justamente lo que hay que probar (el refresh transparente). Alineado con la regla del proyecto de no mockear lo que se está probando.

## Risks / Trade-offs

- **[Falta el endpoint de bootstrap de sesión]** → El guard/menú necesitan permisos efectivos del cliente. **Mitigación**: confirmar/crear `GET /api/auth/session` antes de implementar el guard (Open Question OQ-1). Hasta entonces, la feature `auth-flow` (login/2FA/reset/logout) puede implementarse completa; el guard/menú dependen de OQ-1.
- **[Refresh storm rompe la sesión]** → Sin single-flight, refresh concurrentes invalidan la cadena. **Mitigación**: D3 (single-flight obligatorio) + test explícito de N peticiones concurrentes con un solo refresh.
- **[XSS con token en memoria]** → React escapa por defecto; evitar `dangerouslySetInnerHTML`. **Mitigación**: access token en memoria (D2), nunca en storage; CSP a futuro (no en scope).
- **[Recarga pierde el access token]** → **Mitigación**: bootstrap por refresh al arranque (D2); si no hay refresh válido → login, comportamiento correcto.
- **[Acoplamiento al shape de errores de C-03]** → si C-03 cambia `code`, rompe el mapeo. **Mitigación**: centralizar el mapeo en `auth/services` y tiparlo; los `code` están fijados en la spec archivada de C-03.

## Migration Plan

Proyecto nuevo, sin migración de datos. Pasos de despliegue:
1. Crear `frontend/` con scaffolding y verificar `npm run dev` / build (build SOLO si el usuario lo pide — regla dura #1).
2. (Opcional, fuera de scope estricto) agregar servicio `frontend` a docker-compose dev como TODO.
No hay rollback de datos; revertir = borrar el directorio `frontend/`.

## Open Questions

- **OQ-1 (bloquea el guard, no el resto)**: ¿Existe o se crea `GET /api/auth/session` que devuelva `{user, roles, permissions[]}`? Si C-04 no lo expone, el guard/menú quedan bloqueados hasta cerrarlo. **Opciones**: (a) agregar el endpoint como mini-cambio backend (C-04.x), (b) incluir su spec+tasks de backend dentro del apply de C-21. Decisión recomendada: (a), para mantener C-21 frontend-only. **Resolver antes de las tasks del guard.**
- **OQ-2**: ¿`tenant_codigo` se ingresa en el login o se infiere del subdominio/host? FL-01 lo trata como dato del login; C-03 lo exige en el body. Por defecto: campo en el formulario de login (puede prellenarse desde el host a futuro).
- **OQ-3**: ¿Alcance del enroll de 2FA en C-21? Por defecto: solo se cubre el `verify` en login; el enroll wizard (QR) queda como TODO o mínimo.
