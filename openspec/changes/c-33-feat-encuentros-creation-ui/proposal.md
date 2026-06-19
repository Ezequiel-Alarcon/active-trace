## Why

El backend de encuentros (C-13 archivado) ya expone `POST /api/encuentros/slots` y `POST /api/encuentros/instancias/unico`, pero el frontend solo tiene visualización/read-only. Los coordinadores y profesores no pueden crear encuentros recurrentes (F6.1) ni únicos (F6.2) desde la UI — obligando a usar el API directamente o dejando la funcionalidad incompleta. Este change llena ese gap.

## What Changes

- **SlotForm component**: formulario de creación de slot recurrente con wizard de 4 pasos (materia → día/hora → duración → preview → crear)
- **InstanciaUnicaForm component**: formulario de encuentro único (fecha, hora, materia, modalidad, link)
- **EncuentrosPage**: extiende con tab "Crear slot" y "Crear único" (requiere permiso `encuentros:gestionar`)
- **useCreateSlot() hook**: mutation para crear slot vía `POST /api/encuentros/slots`
- **useCreateInstanciaUnica() hook**: mutation para crear instancia única vía `POST /api/encuentros/instancias/unico`
- **SlotFormWizard**: stepper visual para guiar la creación de slot recurrente
- **MateriaSelector component**: selector de materia con búsqueda (reutilizable para ambos forms)
- **PreviewStep**: muestra preview de las N instancias que se van a generar antes de confirmar

## Capabilities

### New Capabilities

- `frontend-encuentros-creation`: formularios y hooks para crear slots recurrentes (F6.1) y encuentros únicos (F6.2) desde la UI. Consume endpoints del backend de C-13.

### Modified Capabilities

- `frontend-encuentros-admin`: extiende la página existente `EncuentrosPage` con tabs adicionales de creación (no modifica specs de visualización existentes — solo adiciona secciones nuevas)

## Impact

- **Archivos frontend**: `frontend/src/features/encuentros/components/SlotForm.tsx`, `InstanciaUnicaForm.tsx`, `SlotFormWizard.tsx`, `MateriaSelector.tsx`, `PreviewStep.tsx`; hooks `useCreateSlot.ts`, `useCreateInstanciaUnica.ts`; extensión de `EncuentrosPage.tsx`
- **APIs consumidas**: `POST /api/encuentros/slots`, `POST /api/encuentros/instancias/unico`
- **Permisos**: `encuentros:gestionar` (COORDINADOR, ADMIN)
- **Dependencias**: C-13 (backend encuentros existe), C-21 (frontend shell existe)
