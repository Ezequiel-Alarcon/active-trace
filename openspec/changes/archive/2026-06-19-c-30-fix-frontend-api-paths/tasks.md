## 1. liquidacionesApi.ts — GET /api/liquidaciones

- [x] 1.1 Cambiar `GET /api/liquidaciones` → `POST /api/liquidaciones/calcular`
- [x] 1.2 Ajustar query params → body JSON `{cohorte_id, periodo}` (periodo = YYYY-MM); remover `docenteId` (backend no lo acepta)

## 2. liquidacionesApi.ts — Paths de salarios

- [x] 2.1 Cambiar paths `POST /salarios-base` → `POST /salarios/base` y `POST /salarios-plus` → `POST /salarios/plus`
- [x] 2.2 Verificar PATCH/DELETE para salarios — **NO existen** en backend (solo POST para creación)
- [x] 2.3 Remover del frontend: `fetchSalariosBase`, `fetchSalariosPlus`, `updateSalarioBase`, `updateSalarioPlus`, `deleteSalarioBase`, `deleteSalarioPlus` (sin backend); limpiar `useGrillaSalarial.ts`

## 3. equiposApi.ts — Path de exportar

- [x] 3.1 Cambiar `/exportar/${equipoId}` → `/exportar?materia_id=...&cohorte_id=...` (GET con query params)
- [x] 3.2 `AsignacionResponse` tiene `materia_id` disponible; `exportarEquipo(materiaId, cohorteId, rolId?)` y hook actualizado

## 4. encuentrosApi.ts — Path incorrecto

- [x] 4.1 Cambiar `GET /api/encuentros` → `GET /api/encuentros/instancias`
- [x] 4.2 Filtros: `materia` → `materia_id`; remover `docente` (backend no lo soporta); `cohorte_id` es opcional en backend

## 5. UsuarioFormModal.tsx — Verificacion PII

- [x] 5.1 ✅ No hay `console.log` de DNI/CUIL en el componente — verificado con grep
- [x] 5.2 Los TODOs referenciaban C-29 (para `Comunicacion.destinatario`), no `Usuario.dni/cuil`. C-07 (usuarios-y-asignaciones) ya implementó el cifrado AES-256 para `Usuario.dni/cuil`. TODOs actualizados para clarificar que el cifrado es transparente al frontend y referencian C-07.