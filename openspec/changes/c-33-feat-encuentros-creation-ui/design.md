## Context

El backend de encuentros (C-13) expone `POST /api/encuentros/slots` y `POST /api/encuentros/instancias/unico`. El frontend existente `EncuentrosPage` solo tiene visualización en tabs (encuentros, slots, guardias) sin capacidad de creación. F6.1 y F6.2 de la KB requieren formularios para crear slots recurrentes y encuentros únicos.

Stack frontend: React 18 + TypeScript + TanStack Query + React Hook Form + Zod + Tailwind. Componentes UI en `@/shared/ui`. Feature-based structure en `frontend/src/features/encuentros/`.

**Nota conocida**: hay un TODO en `encuentrosApi.ts:4-5` que señala que el frontend llama `GET /api/encuentros` pero el backend tiene el endpoint en `GET /api/encuentros/instancias`. Esto afecta solo al fetch de lectura (ya existe), no a los endpoints de creación que usan paths correctos (`/api/encuentros/slots`, `/api/encuentros/instancias/unico`).

## Goals / Non-Goals

**Goals:**
- Formulario de creación de slot recurrente con wizard/stepper de 4 pasos (materia → día/hora → duración → preview → crear)
- Formulario de creación de encuentro único (fecha, hora, materia, modalidad, link, duración)
- Extender `EncuentrosPage` con tabs "Crear slot" y "Crear único"
- Hooks `useCreateSlot()` y `useCreateInstanciaUnica()` con TanStack Query mutations
- Preview de instancias generadas antes de confirmar (muestra las N fechas que se van a crear)

**Non-Goals:**
- Backend de encuentros (ya existe, C-13 archivado)
- Edición de slots o instancias individuales (F6.3 — no incluido)
- Visualización mejorada de encuentros (ya existe)
- Funcionalidad de guardias (ya existe)

## Decisions

**1. Wizard de 4 pasos para slot recurrente**

Alternativa descartada: formulario único con todos los campos.
Razón: la creación de slot tiene 5+ campos y la preview de instancias generadas upfront (RN-13) es información clave que el usuario debe ver ANTES de confirmar. Un stepper reduce cognición y permite validación progresiva.

Estructura del wizard:
1. **Paso 1 — Materia**: selector de materia (requerido)
2. **Paso 2 — Día/Hora**: día de semana, hora inicio, hora fin, modalidad (virtual/presencial), link meet/video
3. **Paso 3 — Duración**: fecha inicio, cantidad de semanas (default 16, min 1, max 52)
4. **Paso 4 — Preview**: tabla con las N fechas generadas, botón "Crear"

**2. Componente MateriaSelector reutilizable**

Se crea `MateriaSelector` como componente standalone porque es necesario en ambos formularios (slot y único). Expone `materia_id` como valor seleccionado.

**3. React Hook Form + Zod para validación**

Siguiendo la convención del proyecto. Zod schemas en `types/encuentros.ts` o schema dedicado.

**4. Mutaciones con TanStack Query `useMutation`**

`useCreateSlot()` → `POST /api/encuentros/slots`
`useCreateInstanciaUnica()` → `POST /api/encuentros/instancias/unico`
Invalidación de `['slots']` o `['encuentros']` tras creación exitosa.

**5. Permiso `encuentros:gestionar`**

Ambos formularios solo visibles para roles con `encuentros:gestionar` (COORDINADOR, ADMIN). Se implementa con route guard ya existente (C-21).

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Wizard con state local puede perder datos si el usuario cierra sin guardar | Persistir state del wizard en sessionStorage keyed por feature; limpiar al completar |
| API de creación retorna errores de validación (422) | Mostrar errores inline bajo cada campo usando `formState.errors` de React Hook Form |
| Preview de instancias generadas no coincide con backend | El preview es cálculo 100% client-side (fecha_inicio + N semanas); el backend genera las mismas instancias,的一致 es garantizada por RN-13 |
| Selector de materia necesita cargar lista | Usar `useQuery` con staleTime largo; fallback a input con búsqueda manual si el catálogo es pequeño |
