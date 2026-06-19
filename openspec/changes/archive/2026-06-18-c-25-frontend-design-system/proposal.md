## Why

Las 10 pantallas core del frontend (login, importación, comisión, atrasados, ranking, notas finales, reportes, entregas sin corregir, comunicaciones, monitor) ya están implementadas y funcionan, pero su estilado es ad-hoc: cada página repite clases de Tailwind, los colores de estado (atrasado, aprobado, pendiente, estados de cola) no son consistentes entre vistas y no existe una capa de componentes de presentación reutilizable. Esto genera duplicación, dificulta el mantenimiento y produce una experiencia visual desprolija. Se diseñó en Stitch un lenguaje visual coherente para estas pantallas; corresponde aterrizarlo en código de forma sistemática, sin reescribir la lógica ya probada.

## What Changes

- Se introduce una **capa de componentes de presentación reutilizables** (design system) en `frontend/src/shared/ui/`: `Button`, `Card`, `Badge`, `StatusBadge`, `DataTable`, `KpiCard`, `FilterBar`, `EmptyState`, `PageHeader`.
- Se centraliza el **lenguaje visual** (tokens de color, espaciado y tipografía) y los **colores semánticos de estado**: rojo = atrasado/fallido, verde = aprobado/enviado, ámbar = pendiente/cancelado, azul = en envío/acento primario, gris = neutro/pendiente-cola.
- Se **re-estila el shell** (`AppLayout`) y las **10 páginas existentes** para que consuman la capa UI, eliminando la duplicación de clases Tailwind.
- Se **preserva intacta** toda la lógica de negocio: hooks de TanStack Query, guards RBAC, identidad desde sesión, máquina de pasos de comunicaciones, estados de carga/error y los tests existentes. **NO BREAKING**: no cambian rutas, contratos de datos, permisos ni comportamiento observable funcional.

## Capabilities

### New Capabilities
- `frontend-design-system`: capa de componentes de presentación reutilizables y tokens visuales (colores, espaciado, tipografía, colores semánticos de estado) que estandarizan la UI del frontend. Define los primitivos accesibles (`Button`, `Card`, `Badge`, `StatusBadge`, `DataTable`, `KpiCard`, `FilterBar`, `EmptyState`, `PageHeader`) y sus contratos de props.
- `frontend-ui-restyle`: adopción del design system por el shell (`AppLayout`) y las 10 páginas core, garantizando consistencia visual y semántica entre vistas sin alterar el comportamiento funcional existente.

### Modified Capabilities
<!-- El comportamiento de frontend-app-shell, frontend-auth-flow y las páginas de C-22 no cambia a nivel de requisitos: el restyle es presentacional y preserva nav, permisos, identidad desde sesión y flujos. No se modifican specs de requisitos existentes. -->

## Impact

- **Código nuevo**: `frontend/src/shared/ui/*` (componentes primitivos + tests + barrel export), `frontend/src/shared/ui/tokens.ts` (o `tailwind.config` extendido con la paleta semántica).
- **Código modificado**: `frontend/src/shared/components/AppLayout.tsx` y las 10 páginas/componentes de presentación de `features/{auth,calificaciones,comision,analisis,entregas,comunicacion,monitor}`. Solo capa de markup/estilos; los hooks y la lógica quedan iguales.
- **Configuración**: posible extensión de `frontend/tailwind.config.js` con la paleta y tokens semánticos (hoy `theme.extend` está vacío).
- **Sin impacto** en: backend, APIs, base de datos, rutas, permisos RBAC, contratos de datos. Los tests existentes deben seguir pasando (no regresión).
- **Fuente de diseño**: proyecto Stitch "Active Trace — Pantallas Core" (10 screens) como referencia visual.
- **Governance**: LOW (presentación frontend, sin lógica crítica). El restyle del shell preserva la lógica de identidad/permisos sin tocarla.
