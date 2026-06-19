## Context

El frontend (React + TanStack Query) consume endpoints definidos en `services/*.ts` bajo `features/`. El backend (FastAPI) define sus routers con paths específicos. La desincronización ocurre cuando:
1. El frontend usa un método HTTP diferente al del backend
2. El frontend usa un path diferente al declarado en el router
3. El frontend pasa parámetros como path params cuando el backend espera query params

## Goals / Non-Goals

**Goals:**
- Corregir todos los paths de API para que el frontend pueda comunicarse con el backend
- Mantener la semántica RESTful del backend (no cambiar el backend para适应 el frontend)

**Non-Goals:**
- No modificar lógica de negocio del backend
- No crear nuevos endpoints en backend (solo sincronizar el frontend)
- No abordar cifrado PII (eso es C-29)

## Decisions

### Decision 1: Liquidaciones — cambiar frontend de GET a POST

**Choice**: Modificar `liquidacionesApi.ts` para usar POST en lugar de GET.

**Rationale**: El backend tiene `POST /api/liquidaciones/calcular` que acepta body JSON con `{cohorte_id, periodo}`. GET con query params no es apropiado para la complejidad de filtros de liquidaciones. POST permite pasar un DTO tipado.

**Alternatives considered**:
- Crear GET `/api/liquidaciones/periodo` en backend — rejected: no quiere fragmentar la API con endpoints similares

### Decision 2: Liquidaciones salarios — sincronizar paths

**Choice**: Cambiar `/api/liquidaciones/salarios-base` → `/api/liquidaciones/salarios/base`

**Rationale**: El backend ya tiene la estructura `/api/liquidaciones/salarios/base`. El frontend debe alinearse.

### Decision 3: Equipos exportar — cambiar a query params

**Choice**: Modificar frontend para usar `/exportar?materia_id=...&cohorte_id=...` en lugar de `/exportar/${equipoId}`

**Rationale**: La spec `equipos-export` define claramente que el endpoint acepta query params. El frontend estaba usando un path param `equipoId` que no existe en el backend.

**Alternatives considered**:
- Crear endpoint RESTful `/exportar/{materia_id}/{cohorte_id}` — rejected: cambia la semántica de la spec existente

### Decision 4: Encuentros — cambiar a `/instancias`

**Choice**: Cambiar `GET /api/encuentros` → `GET /api/encuentros/instancias`

**Rationale**: La spec `encuentros-instancias` define el endpoint con ese path. El frontend tenía un atajo incorrecto.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| El frontend espera un formato de respuesta diferente al que devuelve el backend | Verificar response types en cada fix |
| Cambios en frontend rompen otros consumidores del API | Estos endpoints son internos del frontend, no son públicos |

## Open Questions

Ninguna — todos los paths están definidos en specs archivadas y el código backend ya existe.