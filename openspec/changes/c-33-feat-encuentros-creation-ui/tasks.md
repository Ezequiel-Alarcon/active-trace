## 1. API layer — types y servicios

- [ ] 1.1 Agregar `CreateSlotRequest` y `CreateInstanciaUnicaRequest` types en `frontend/src/features/encuentros/types/encuentros.ts`
- [ ] 1.2 Agregar `createSlot()` en `frontend/src/features/encuentros/services/encuentrosApi.ts` (`POST /api/encuentros/slots`)
- [ ] 1.3 Agregar `createInstanciaUnica()` en `frontend/src/features/encuentros/services/encuentrosApi.ts` (`POST /api/encuentros/instancias/unico`)

## 2. Hooks — mutations de creación

- [ ] 2.1 Crear `useCreateSlot()` hook en `frontend/src/features/encuentros/hooks/useCreateSlot.ts` (usa `useMutation`, invalida `['slots']`)
- [ ] 2.2 Crear `useCreateInstanciaUnica()` hook en `frontend/src/features/encuentros/hooks/useCreateInstanciaUnica.ts` (usa `useMutation`, invalida `['encuentros']`)
- [ ] 2.3 Crear `useMaterias()` hook en `frontend/src/features/encuentros/hooks/useMaterias.ts` (para MateriaSelector)

## 3. Componentes — SlotForm wizard

- [ ] 3.1 Crear `MateriaSelector.tsx` en `frontend/src/features/encuentros/components/` — input con búsqueda de materias
- [ ] 3.2 Crear `SlotFormStep1Materia.tsx` — paso 1 del wizard (solo MateriaSelector)
- [ ] 3.3 Crear `SlotFormStep2DayTime.tsx` — paso 2 (día de semana, hora inicio/fin, modalidad, link)
- [ ] 3.4 Crear `SlotFormStep3Duration.tsx` — paso 3 (fecha inicio, cantidad de semanas, título)
- [ ] 3.5 Crear `PreviewStep.tsx` — paso 4 (tabla con N fechas generadas client-side)
- [ ] 3.6 Crear `SlotFormWizard.tsx` — stepper que orchestra los 4 pasos + estado del wizard en sessionStorage

## 4. Componentes — InstanciaUnicaForm

- [ ] 4.1 Crear `InstanciaUnicaForm.tsx` en `frontend/src/features/encuentros/components/` — formulario completo con todos los campos

## 5. Página — extender EncuentrosPage

- [ ] 5.1 Agregar tab "Crear slot" a `EncuentrosPage.tsx` con `SlotFormWizard`
- [ ] 5.2 Agregar tab "Crear único" a `EncuentrosPage.tsx` con `InstanciaUnicaForm`
- [ ] 5.3 Envolver ambos formularios con verificación de permiso `encuentros:gestionar` (ocultar tabs si no hay permiso)

## 6. Validación y UX

- [ ] 6.1 Agregar Zod schemas de validación para `CreateSlotRequest` e `InstanciaUnicaRequest`
- [ ] 6.2 Validación inline con `formState.errors` de React Hook Form en ambos forms
- [ ] 6.3 Persistir estado del wizard en sessionStorage (key: `encuentros-slot-wizard`)
- [ ] 6.4 Mostrar errores de API (422) inline en los campos correspondientes

## 7. Tests

- [ ] 7.1 Test para `useCreateSlot` hook (mock de API, éxito y error)
- [ ] 7.2 Test para `useCreateInstanciaUnica` hook (mock de API, éxito y error)
- [ ] 7.3 Test para wizard stepper (navegación entre pasos, validación por paso)
- [ ] 7.4 Test para `PreviewStep` (cálculo correcto de N fechas)
- [ ] 7.5 Test para `InstanciaUnicaForm` (validación, submit)
