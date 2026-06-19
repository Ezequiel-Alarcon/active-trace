## Context

Las 10 páginas core del frontend ya están implementadas (C-21 shell+auth, C-22 academico-docente) con su lógica de datos (TanStack Query), guards RBAC y tests. El estilado es ad-hoc: clases de Tailwind repetidas por página, colores de estado inconsistentes y sin componentes de presentación compartidos. `frontend/tailwind.config.js` tiene `theme.extend` vacío. El shell (`AppLayout.tsx`) ya establece el lenguaje visual base: header blanco, sidebar 224px gris claro, ítem activo `blue-100`/`blue-700`, acento `blue-600`. Se diseñó en Stitch ("Active Trace — Pantallas Core", 10 screens) un lenguaje visual coherente que se quiere aterrizar en código de forma sistemática y sin reescribir la lógica probada.

## Goals / Non-Goals

**Goals:**

- Extraer una capa de componentes de presentación reutilizables en `frontend/src/shared/ui/`.
- Centralizar tokens visuales y colores semánticos de estado (una única fuente de verdad).
- Re-estilar el shell y las 10 páginas para consumir la capa UI, eliminando duplicación.
- Cero regresión funcional: todos los tests existentes siguen pasando; comportamiento observable intacto.
- Cumplir reglas duras: componentes <200 LOC, PascalCase, sin `any`, Tailwind sin inline, fetch solo por hooks.

**Non-Goals:**

- NO se modifican rutas, contratos de datos, permisos RBAC ni endpoints.
- NO se reescribe la lógica de hooks, la máquina de pasos de comunicaciones ni los flujos.
- NO se agregan dependencias de librerías de componentes (Material UI, shadcn, etc.) — se construye sobre Tailwind propio.
- NO se cubren las páginas de épicas aún no construidas (liquidaciones, auditoría, equipos, coloquios, encuentros): quedan para C-23/C-24.

## Decisions

**1. Capa UI propia sobre Tailwind, no librería externa.**
Se construyen primitivos propios (`Button`, `Card`, `Badge`, `StatusBadge`, `DataTable`, `KpiCard`, `FilterBar`, `EmptyState`, `PageHeader`) con `class-variance` manual (objetos de mapeo variante→clases) en vez de adoptar Material UI / shadcn. Rationale: el stack ya define Tailwind como único sistema de estilos y prohíbe CSS modules; sumar una librería de componentes contradice las convenciones y agrega peso. Alternativa descartada: shadcn/ui (genera buenos componentes pero impone Radix + estructura propia, fricción con las reglas y el código existente).

**2. Colores semánticos como mapa centralizado, no clases sueltas.**
Se define un mapa `estado → clases` (ej. `atrasado: 'bg-red-100 text-red-700'`) en un único módulo (`shared/ui/estado-colores.ts`) consumido por `StatusBadge`. Rationale: hoy cada vista escribe sus propias clases de color; centralizar garantiza el requisito de consistencia entre vistas y un único punto de cambio. Alternativa descartada: extender `tailwind.config` con colores nombrados — válido pero no resuelve el mapeo estado→estilo de badge, que igual necesita una capa de lógica.

**3. DataTable genérico tipado, render-prop por columna.**
`DataTable<T>` recibe `columns: { header, render: (row: T) => ReactNode }[]` y `rows: T[]`, con selección opcional. Rationale: las tablas de atrasados, ranking, notas, entregas y monitor comparten estructura pero distintas columnas; un genérico tipado evita duplicar `<table>` y respeta "sin `any`". El estado vacío se delega a `EmptyState`.

**4. Restyle página por página, preservando el árbol de componentes existente.**
Se reemplaza solo el markup de presentación (contenedores, tablas, badges, botones) por los primitivos; los hooks, props de datos y la lógica de pasos NO se tocan. Rationale: minimiza el riesgo de regresión y mantiene los tests verdes. El `comisionId` por `useOutletContext`, los `useState` de pasos y los hooks de query quedan idénticos.

**5. Strict TDD para los primitivos UI; restyle de páginas validado por no-regresión.**
Los componentes de `shared/ui/` se construyen con test-first (RED→GREEN→triangulación→refactor) porque tienen comportamiento testeable (variantes, disabled, estado vacío, mapeo de color). El restyle de páginas se valida ejecutando los tests existentes (que deben seguir pasando) más asserts visuales mínimos donde aporten. Rationale: los primitivos son lógica nueva; el restyle es transformación de markup cubierta por los tests previos.

## Risks / Trade-offs

- **[Romper tests existentes que asertan clases CSS específicas]** → Mitigación: identificar tests que dependan de clases concretas antes de re-estilar; preferir asserts por rol/texto/aria. Correr la suite tras cada página.
- **[Inconsistencia si una página se salta la capa UI]** → Mitigación: el spec exige adopción en las 10 páginas; revisar en code review que ninguna defina colores de estado ad-hoc.
- **[Componentes que superen 200 LOC al agregar variantes]** → Mitigación: separar mapas de variantes a módulos auxiliares (`estado-colores.ts`, `button-variants.ts`) y mantener el componente delgado.
- **[Stitch genera HTML con paleta levemente distinta a la del shell actual]** → Mitigación: la fuente de verdad del color es el shell existente (`blue-100/700`, `blue-600`), no el HTML crudo de Stitch; Stitch es referencia de layout, no de tokens exactos.

## Migration Plan

1. Crear tokens + mapa de colores semánticos (`shared/ui/estado-colores.ts`, extensión opcional de `tailwind.config`).
2. Construir primitivos UI con TDD, uno por uno, con barrel export `shared/ui/index.ts`.
3. Re-estilar el shell (`AppLayout`) y correr sus tests.
4. Re-estilar las páginas en orden de menor a mayor riesgo (login → tablas → comunicaciones multi-step), corriendo tests tras cada una.
5. Rollback: el cambio es puramente frontend y reversible por revert de commits; no hay migraciones de datos ni cambios de contrato.

## Open Questions

- ¿Se extiende `tailwind.config` con tokens nombrados o se mantienen clases utilitarias directas en el mapa de colores? (Decisión por defecto: mapa de clases utilitarias; extender config solo si aparece repetición de valores no utilitarios.)
- ¿Algún test existente asierta clases Tailwind específicas que obliguen a ajustar el assert? (A relevar en la fase de apply, página por página.)
