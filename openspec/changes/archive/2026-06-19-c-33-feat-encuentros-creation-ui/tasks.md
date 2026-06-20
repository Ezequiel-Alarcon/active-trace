## 1. API layer — types y servicios

- [x] 1.1 Agregar `CreateSlotRequest` y `CreateInstanciaUnicaRequest` types en `frontend/src/features/encuentros/types/encuentros.ts` incluyendo `cohorte_id` requerido en ambos
- [x] 1.2 Agregar `createSlot()` en `frontend/src/features/encuentros/services/encuentrosApi.ts` (`POST /api/encuentros/slots`)
- [x] 1.3 Agregar `createInstanciaUnica()` en `frontend/src/features/encuentros/services/encuentrosApi.ts` (`POST /api/encuentros/instancias/unico`)

## 2. Hooks — mutations de creación

- [x] 2.1 Crear `useCreateSlot()` hook en `frontend/src/features/encuentros/hooks/useCreateSlot.ts` (usa `useMutation`, invalida `['slots']`)
- [x] 2.2 Crear `useCreateInstanciaUnica()` hook en `frontend/src/features/encuentros/hooks/useCreateInstanciaUnica.ts` (usa `useMutation`, invalida `['encuentros']`)
- [x] 2.3 Crear `useMaterias()` hook en `frontend/src/features/encuentros/hooks/useMaterias.ts` (para `MateriaSelector`)
- [x] 2.4 Crear `useCohortes()` hook en `frontend/src/features/encuentros/hooks/useCohortes.ts` (para `CohorteSelector`, con opciones desde datos existentes del tenant/dominio)

## 3. Componentes — SlotForm wizard

- [x] 3.1 Crear `MateriaSelector.tsx` en `frontend/src/features/encuentros/components/` — input con búsqueda de materias
- [x] 3.2 Crear `CohorteSelector.tsx` en `frontend/src/features/encuentros/components/` — selector explícito de cohortes reutilizable
- [x] 3.3 Crear `SlotFormStep1ContextoAcademico.tsx` — paso 1 del wizard (`MateriaSelector` + `CohorteSelector`)
- [x] 3.4 Crear `SlotFormStep2DayTime.tsx` — paso 2 (día de semana, hora inicio/fin, modalidad, link)
- [x] 3.5 Crear `SlotFormStep3Duration.tsx` — paso 3 (fecha inicio, cantidad de semanas, titulo)
- [x] 3.6 Crear `PreviewStep.tsx` — paso 4 (tabla con N fechas generadas client-side)
- [x] 3.7 Crear `SlotFormWizard.tsx` — stepper que orchestra los 4 pasos + estado del wizard en sessionStorage

## 4. Componentes — InstanciaUnicaForm

- [x] 4.1 Crear `InstanciaUnicaForm.tsx` en `frontend/src/features/encuentros/components/` — formulario completo con `MateriaSelector`, `CohorteSelector` y resto de campos

## 5. Página — extender EncuentrosPage

- [x] 5.1 Agregar tab "Crear slot" a `EncuentrosPage.tsx` con `SlotFormWizard`
- [x] 5.2 Agregar tab "Crear único" a `EncuentrosPage.tsx` con `InstanciaUnicaForm`
- [x] 5.3 Envolver ambos formularios con verificación de permiso `encuentros:gestionar` (ocultar tabs si no hay permiso)

## 6. Validación y UX

- [x] 6.1 Agregar Zod schemas de validación para `CreateSlotRequest` e `InstanciaUnicaRequest`, con `cohorte_id` obligatorio en ambos
- [x] 6.2 Validación inline con `formState.errors` de React Hook Form en ambos forms
- [x] 6.3 Persistir estado del wizard en sessionStorage (key: `encuentros-slot-wizard`)
- [x] 6.4 Mostrar errores de API (422) inline en los campos correspondientes

## 7. Tests

- [x] 7.1 Test para `useCreateSlot` hook (mock de API, éxito y error)
- [x] 7.2 Test para `useCreateInstanciaUnica` hook (mock de API, éxito y error)
- [x] 7.3 Test para wizard stepper (navegación entre pasos, validación por paso, bloqueo si falta `cohorte_id`)
- [x] 7.4 Test para `PreviewStep` (cálculo correcto de N fechas)
- [x] 7.5 Test para `InstanciaUnicaForm` (validación de `cohorte_id`, submit)
