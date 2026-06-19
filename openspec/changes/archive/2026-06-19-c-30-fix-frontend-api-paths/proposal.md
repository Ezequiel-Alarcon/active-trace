## Why

El frontend consume endpoints de API que no existen o usan paths incorrectos en las áreas de liquidaciones, equipos y encuentros. Esto causa errores 404 en runtime, impidiendo que los usuarios accedan a funcionalidades críticas. La raíz es un desincronización entre los paths declarados en los servicios de TanStack Query y los endpoints realmente implementados en el backend FastAPI.

## What Changes

- **liquidacionesApi.ts**: GET `/api/liquidaciones` → cambiar a POST `/api/liquidaciones/calcular` con body JSON `{cohorte_id, periodo}`
- **liquidacionesApi.ts**: `POST /salarios-base` y `POST /salarios-plus` → sincronizar con `POST /salarios/base` y `POST /salarios/plus`. GET/PATCH/DELETE para salarios **no existen** en backend (solo POST para creación) — esas funciones fueron removidas del frontend
- **equiposApi.ts**: `/exportar/${equipoId}` path param → cambiar a `/exportar?materia_id=...&cohorte_id=...` query params
- **encuentrosApi.ts**: GET `/api/encuentros` → cambiar a GET `/api/encuentros/instancias`
- **UsuarioFormModal.tsx**: Verificar que no se expone PII en logs (DNI/CUIL en texto plano)

## Capabilities

### New Capabilities
None — este es un bugfix de sincronización, no introduce nuevas capacidades.

### Modified Capabilities
None — los cambios son de alineación de paths, no modifican requisitos de specs existentes.

## Impact

### Archivos affected

**Frontend:**
- `frontend/src/features/liquidaciones/services/liquidacionesApi.ts`
- `frontend/src/features/liquidaciones/hooks/useLiquidaciones.ts`
- `frontend/src/features/liquidaciones/hooks/useGrillaSalarial.ts`
- `frontend/src/features/equipos/services/equiposApi.ts`
- `frontend/src/features/equipos/hooks/useEquipos.ts`
- `frontend/src/features/encuentros/services/encuentrosApi.ts`
- `frontend/src/features/admin/components/UsuarioFormModal.tsx`

### Dependencias archivadas
- C-18 (liquidaciones-y-honorarios) — archivado
- C-08 (equipos-docentes) — archivado
- C-13 (encuentros-y-guardias) — archivado