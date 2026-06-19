## Context

Este change construye los feature modules frontend para los roles FINANZAS y ADMIN. Actualmente no existe UI para liquidaciones, facturas, estructura académica, usuarios del tenant ni auditoría — solo backend APIs de C-06, C-07, C-18 y C-19. El SPA tiene shell funcional (C-21), design system (C-25), y features académico-docente (C-22). Las nuevas features siguen las mismas convenciones: feature-based modules, TanStack Query, React Hook Form + Zod, `@/shared/ui` primitives.

## Goals / Non-Goals

**Goals:**
- Feature module `features/liquidaciones/` completo: liquidaciones período, cierre, historial, grilla salarial, facturas
- Feature module `features/admin/` completo: estructura académica, usuarios tenant, panel auditoría, log auditoría
- Protección por permiso en rutas y navegación lateral
- Tests de componente e integración con mocks HTTP para cada página y hook

**Non-Goals:**
- No se modifican APIs backend existentes
- No se implementa lógica de negocio en frontend (solo presentación + fetch)
- No se construyen componentes UI nuevos (se reusan los de `@/shared/ui`)
- No se toca auth, shell, ni features existentes

## Decisions

1. **Separación en dos feature modules**: `liquidaciones/` (FINANZAS) y `admin/` (ADMIN). Cada uno con su estructura types/services/hooks/components/pages. Sigue el mismo patrón que `analisis/` y `comunicacion/`.

2. **Estructura académica como ABM en página única con tabs**: Carreras, Cohortes y Materias comparten una página `/admin/estructura` con tabs o secciones separadas. Cada sección es un CRUD completo (DataTable + modal/form). Se evita crear tres páginas separadas porque son entidades pequeñas y relacionadas.

3. **Grilla salarial en página única con tabs**: SalarioBase y SalarioPlus en la misma página `/admin/liquidaciones/grilla` por la misma razón — son tablas pequeñas con vigencia.

4. **Facturas como página separada**: `/admin/liquidaciones/facturas` con filtros (docente, estado, rango fechas) + DataTable + acción de cambio de estado. Suficiente complejidad para standalone.

5. **Auditoría: panel + log como dos vistas**: `/admin/auditoria` para el dashboard con KPIs y `/admin/auditoria/log` para el log detallado con filtros. El panel usa KpiCard para métricas y DataTable para últimas acciones. El log usa FilterBar + DataTable con paginación.

6. **Rutas anidadas bajo `/admin`**: todas las rutas ADMIN bajo `/admin/*` y las de liquidaciones también bajo `/admin/liquidaciones/*`. Esto simplifica la navegación y agrupa funcionalidades de gestión.

7. **Mismos patrones de fetch que features existentes**: cada endpoint tiene su función en `services/*Api.ts`, hook TanStack Query en `hooks/`, tipos en `types/`. HTTP mocking con `@/test/server` (MSW).

8. **Navegación condicional por permiso**: entradas en `AppLayout.tsx` filtradas con `hasPermission()` como ya se hace con Comisión/Monitor/Comunicaciones.

## Risks / Trade-offs

- **[Risk] Tamaño del change**: 2 feature modules con 9 capacidades es grande. → Mitigación: son páginas de CRUD/tabla que siguen patrones repetitivos; el código es boilerplate predecible.
- **[Risk] Dependencia de C-23**: si C-23 modifica `shared/router.tsx` o `AppLayout.tsx`, puede haber conflicto. → Mitigación: C-24 y C-23 son paralelizables; si hay conflicto, se resuelve en merge.
- **[Trade-off] Sin formularios lazy**: los ABM usan modales simples en lugar de páginas separadas para edición. Ahorra navegación pero puede ser menos mobile-friendly (aceptable porque FINANZAS/ADMIN son roles desktop).
- **[Risk] Sin tests de mutación para cierre de liquidación**: el cierre es una acción irreversible del lado backend. El frontend solo muestra confirmación y llama a la API. La inmutabilidad se testea en backend (C-18).
