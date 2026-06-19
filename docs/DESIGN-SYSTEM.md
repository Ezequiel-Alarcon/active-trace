# Design System — activia-trace frontend

> **Leé este archivo ANTES de escribir o re-estilar cualquier UI del frontend.**
> Define la capa de presentación reutilizable, los colores semánticos, las reglas de estilado
> y el flujo de trabajo para mantener UNA sola gramática visual en toda la app.
> Establecido en el change **C-25 `frontend-design-system`**.

---

## 1. Principio rector

**Una sola gramática visual, no diez dialectos.** Ninguna página define colores de estado, botones ni
tablas a mano. Todo consume la **capa UI** en `frontend/src/shared/ui/`. Si vas a mostrar un estado,
un botón, una tabla, una métrica o un campo de formulario, **ya existe un primitivo para eso** — usalo.

Si un primitivo no existe y lo necesitás en 2+ lugares, **crealo en `shared/ui/` con TDD** (ver §5), no
copies clases de Tailwind en cada página.

---

## 2. La capa UI — `@/shared/ui`

Punto único de importación. Siempre importá desde el barrel:

```tsx
import { Button, TextField, Card, DataTable, StatusBadge, EmptyState } from '@/shared/ui';
```

| Primitivo | Para qué | Props clave |
|-----------|----------|-------------|
| `Button` | Toda acción clicable | `variant?: 'primary' \| 'secondary' \| 'danger'` (default `primary`), + props nativas de `<button>` |
| `TextField` | Campo de formulario (label + input + error) | `id`, `label`, `error?`; `forwardRef` → compatible con `register` de react-hook-form |
| `Badge` | Pill genérico (sin semántica de color) | props nativas de `<span>` |
| `StatusBadge` | **Estado semántico** (atrasado, enviado, etc.) | `estado: EstadoSemantico`, `children` |
| `Card` | Contenedor con borde + padding | props nativas de `<div>` (incl. `className`) |
| `PageHeader` | Título de página + acciones | `title: string`, `actions?: ReactNode` |
| `EmptyState` | Estado vacío informativo (gris, `role="status"`) | `children` |
| `KpiCard` | Métrica destacada (número grande + etiqueta) | `label: string`, `value: ReactNode` |
| `FilterBar` | Barra de filtros horizontal (flex-wrap) | `children` |
| `DataTable<T>` | Tabla tipada genérica | `columns: Column<T>[]`, `rows: T[]`, `rowKey: (row, index) => string`, `emptyMessage?`, `selection?` |

### `DataTable<T>` en detalle

```tsx
const columns: Column<Alumno>[] = [
  { header: 'Alumno', render: (a) => a.nombre },
  { header: 'Email', render: (a) => <span className="text-gray-500">{a.email}</span> },
  { header: 'Estado', render: (a) => <StatusBadge estado="atrasado">{a.estado}</StatusBadge> },
];

<DataTable
  rows={alumnos}
  columns={columns}
  rowKey={(a, idx) => a.id ?? String(idx)}   // index disponible para ids nulos/duplicados
  emptyMessage="No hay alumnos para esta comisión."
  selection={{                                // opcional: checkbox por fila
    selectedKeys,                             // Set<string>
    onToggle,                                 // (key) => void
    ariaLabel: (a) => `Seleccionar ${a.nombre}`,
  }}
/>
```

- Cuando `rows` está vacío, `DataTable` renderiza `EmptyState` con `emptyMessage` automáticamente.
- La `key` de cada columna es su `header` (mantené headers únicos por tabla).
- Para tipos con index signature (`extends Record<string, unknown>`) **no spreadear** `{...row, _key}`
  (pierde el index signature y rompe el typecheck): usá el `index` del `rowKey`.

---

## 3. Colores semánticos de estado — fuente única

Viven en `shared/ui/estado-colores.ts` y se consumen **solo** vía `StatusBadge`. **Prohibido** escribir
`bg-red-100 text-red-700` (o similar) a mano en una página.

| Estado (`EstadoSemantico`) | Color | Significado |
|----------------------------|-------|-------------|
| `atrasado`, `fallido` | 🔴 rojo (`bg-red-100 text-red-700`) | atraso académico / envío fallido |
| `aprobado`, `enviado` | 🟢 verde (`bg-green-100 text-green-700`) | aprobado / mensaje enviado OK |
| `pendiente`, `cancelado` | 🟡 ámbar (`bg-amber-100 text-amber-700`) | pendiente de corrección / cancelado |
| `en-envio` | 🔵 azul (`bg-blue-100 text-blue-700`) | en proceso de envío |
| `pendiente-cola`, `neutro` | ⚪ gris (`bg-gray-100 text-gray-700`) | pendiente en cola / neutro |

> **Regla de oro:** el **verde es semántico** ("aprobado/enviado"). NUNCA uses verde para un botón de
> acción. La acción primaria es **azul** (`Button variant="primary"`). El verde queda reservado a badges.

Los estados de la **cola de comunicaciones** mapean así: Pendiente→`pendiente-cola` (gris),
En envío→`en-envio` (azul), Enviado→`enviado` (verde), Fallido→`fallido` (rojo), Cancelado→`cancelado` (ámbar).

---

## 4. Lenguaje visual del shell

- **Header**: blanco, borde gris inferior. Marca a la izquierda = cuadradito acento `bg-blue-600` + texto
  "Active Trace" gris oscuro negrita. A la derecha: email (de la sesión) + "Cerrar sesión" en rojo.
- **Sidebar**: 224px (`w-56`), fondo gris claro, ítem activo `bg-blue-100 text-blue-700`, hover `bg-gray-100`,
  con `transition-colors`. Los ítems se filtran por permiso (fail-closed).
- **Main**: blanco, `p-6`.
- **Acento primario**: `blue-600`. **Tipografía**: sans-serif (default de Tailwind). **Idioma**: español rioplatense.

---

## 5. Reglas duras de estilado (fallan en code review)

1. **Importar siempre desde `@/shared/ui`** (barrel), nunca por ruta interna del primitivo.
2. **0 colores de estado ad-hoc en `features/`**. Todo estado → `StatusBadge`. (Auditá con
   `grep -rnE "bg-(red|green|amber|yellow)-100" src/features --include=*.tsx | grep -v .test.`)
3. **0 estilos inline** (`style={...}`) salvo valores genuinamente dinámicos no expresables en Tailwind.
4. **Sin `any`.** TS strict; `Column<T>` y genéricos tipados.
5. **Componentes < 200 LOC.** Si un primitivo crece, extraé sus mapas de variantes a un módulo aparte.
6. **PascalCase** en componente y archivo; default export para los primitivos.
7. **Fetch solo por hooks** (TanStack Query). Los componentes de presentación NO hacen fetch.
8. **El restyle NO toca la lógica.** Hooks, máquina de pasos, guards RBAC e identidad-desde-sesión quedan intactos.

---

## 6. Flujo de trabajo para re-estilar una página existente

Las páginas suelen **ya existir y funcionar**. Re-estilar = cambiar markup/estilos, **no** lógica.
Seguí este ciclo (Strict TDD / no-regresión) **por cada página**:

```
0. SAFETY NET   → leé el/los test(s) del componente. Corré su suite y capturá el baseline verde.
                  Anotá qué textos/labels/roles asertan los tests (NO los rompas).
1. RESTYLE      → reemplazá SOLO el markup de presentación por primitivos de @/shared/ui.
                  Preservá: labels, textos de botón, role="alert"/role="status", asociaciones label↔input.
2. RE-RUN       → corré los tests del componente → deben seguir verdes (cero regresión).
3. TYPECHECK    → `npx tsc --noEmit` (¡Vitest NO typechquea!). Cazá errores que los tests no ven.
4. SUITE        → al cerrar un grupo, corré la suite completa (`npm test`) + typecheck global.
```

### Para un primitivo NUEVO (Strict TDD obligatorio)

```
RED  → escribí el test primero (importa el módulo que aún no existe). Corré → debe fallar.
GREEN→ implementá el mínimo para pasar.
TRIANGULATE → agregá casos con distintos inputs (mínimo happy path + un edge).
REFACTOR → limpiá; los tests siguen verdes. Agregá el primitivo al barrel `index.ts`.
```

Cobertura objetivo de los primitivos: **≥80% líneas** (hoy `shared/ui` está al 100%).
`coverage.include` en `vitest.config.ts` incluye `src/shared/ui/**`.

---

## 7. Governance

- Páginas de presentación frontend → **LOW** (autonomía total si pasan los tests).
- Al re-estilar pantallas de **auth** (Login/Forgot/Reset): se permite tocar **presentación**, pero
  **CERO lógica** (auth es CRÍTICO). No tocar `AuthProvider`, hooks ni manejo de tokens/sesión sin
  aprobación explícita.

---

## 8. Referencia rápida de mapeo (pantallas core → primitivos)

| Pantalla | Primitivos usados |
|----------|-------------------|
| Login / Forgot / Reset | `Card` (+ marca), `TextField`, `Button` |
| Importar calificaciones | `Card`, `Button` |
| Comisión workspace | `PageHeader`, tabs (NavLink azul) |
| Atrasados | `DataTable` + `StatusBadge` (rojo) + `Button` (selección) |
| Ranking | `DataTable` + `StatusBadge` (verde) |
| Notas finales | `DataTable` |
| Entregas sin corregir | `DataTable` + `StatusBadge` (ámbar) + `Button` |
| Reportes | estado informativo (placeholder hasta resolver mapping comisión→materia) |
| Monitor | `FilterBar` + `DataTable` + `Button` |
| Comunicar (tracking) | `Card` + `StatusBadge` para los 5 estados de cola |

---

## 9. Deudas conocidas (al cierre de C-25)

- `AuthProvider.tsx`: error de typecheck pre-existente (`refresh_token` no existe en `LoginResponse`).
  Dominio CRÍTICO; bloquea `npm run build` pero no los tests. Pendiente de un change propio.
- Cobertura global de `test:coverage` bajo el threshold: los forms y pages de **auth** nunca tuvieron
  tests de componente (0%). Candidato a un change de cobertura.
