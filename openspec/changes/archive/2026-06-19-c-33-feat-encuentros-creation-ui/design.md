## Context

El backend de encuentros (C-13) expone `POST /api/encuentros/slots` y `POST /api/encuentros/instancias/unico`. El frontend existente `EncuentrosPage` solo tiene visualización en tabs (encuentros, slots, guardias) sin capacidad de creación. F6.1 y F6.2 de la KB requieren formularios para crear slots recurrentes y encuentros únicos.

La corrección de este change debe respetar el contrato backend actual: ambos payloads de creación requieren `cohorte_id`. Esto además está alineado con la documentación del dominio: `knowledge-base/04_modelo_de_datos.md` indica que una misma materia puede pertenecer a distintas cohortes, `knowledge-base/06_funcionalidades.md` modela estos flujos en clave materia × carrera × cohorte y `knowledge-base/10_preguntas_abiertas.md` mantiene PA-07 abierta sobre la semántica de cohortes. Por lo tanto, `materia_id` no alcanza para inferir una cohorte válida de forma segura.

Stack frontend: React 18 + TypeScript + TanStack Query + React Hook Form + Zod + Tailwind. Componentes UI en `@/shared/ui`. Feature-based structure en `frontend/src/features/encuentros/`.

**Nota conocida**: hay un TODO en `encuentrosApi.ts:4-5` que señala que el frontend llama `GET /api/encuentros` pero el backend tiene el endpoint en `GET /api/encuentros/instancias`. Esto afecta solo al fetch de lectura (ya existe), no a los endpoints de creación que usan paths correctos (`/api/encuentros/slots`, `/api/encuentros/instancias/unico`).

## Goals / Non-Goals

**Goals:**
- Formulario de creación de slot recurrente con wizard/stepper de 4 pasos (materia/cohorte → día/hora → duración → preview → crear)
- Formulario de creación de encuentro único (fecha, hora, materia, cohorte, modalidad, link, duración)
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
1. **Paso 1 — Contexto académico**: selector de materia y selector de cohorte (ambos requeridos antes de avanzar)
2. **Paso 2 — Día/Hora**: día de semana, hora inicio, hora fin, modalidad (virtual/presencial), link meet/video
3. **Paso 3 — Duración**: fecha inicio, cantidad de semanas (default 16, min 1, max 52)
4. **Paso 4 — Preview**: tabla con las N fechas generadas, botón "Crear"

**2. Selectores reutilizables de contexto académico**

Se crean `MateriaSelector` y `CohorteSelector` como componentes standalone porque son necesarios en ambos formularios (slot y único). Exponen `materia_id` y `cohorte_id` como valores seleccionados. `CohorteSelector` debe cargar opciones desde datos existentes del tenant/dominio; no depende de inferencia implícita a partir de `materia_id`.

**3. React Hook Form + Zod para validación**

Siguiendo la convención del proyecto. Zod schemas en `types/encuentros.ts` o schema dedicado. Ambos requests deben declarar `cohorte_id` requerido y bloquear submit si falta.

**4. Mutaciones con TanStack Query `useMutation`**

`useCreateSlot()` → `POST /api/encuentros/slots`
`useCreateInstanciaUnica()` → `POST /api/encuentros/instancias/unico`
Invalidación de `['slots']` o `['encuentros']` tras creación exitosa.

Los tipos de request enviados por estos hooks deben incluir `cohorte_id` junto con `materia_id`, sin transformaciones de inferencia intermedias.

**5. Permiso `encuentros:gestionar`**

Ambos formularios solo visibles para roles con `encuentros:gestionar` (COORDINADOR, ADMIN). Se implementa con route guard ya existente (C-21).

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Wizard con state local puede perder datos si el usuario cierra sin guardar | Persistir state del wizard en sessionStorage keyed por feature; limpiar al completar |
| API de creación retorna errores de validación (422) | Mostrar errores inline bajo cada campo usando `formState.errors` de React Hook Form |
| Preview de instancias generadas no coincide con backend | El preview es calculo 100% client-side (fecha_inicio + N semanas); el backend genera las mismas instancias y RN-13 define ese comportamiento |
| Selector de materia/cohorte necesita cargar listas válidas | Usar hooks de catálogo con `useQuery` y staleTime largo; las opciones deben venir de datos existentes del tenant, no de derivación local |
| PA-07 sigue abierta y la semántica final de cohorte puede cambiar | Mantener el contrato UI explícito con `cohorte_id`; si el dominio cambia, se ajusta el origen/opciones del selector, no se vuelve a inferir desde materia |
