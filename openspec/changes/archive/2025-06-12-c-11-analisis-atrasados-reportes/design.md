# C-11: Analisis de Atrasados y Reportes — Design

## Context

C-09 implementó `VersionPadron` + `EntradaPadron` (actividades esperadas por materia/cohorte). C-10 implementó `Calificacion` (nota por actividad), `UmbralMateria` (umbral_pct por asignacion), y la función `derivar_aprobado(nota, umbral_pct, conjunto_aprobado)`.

Este change aprovecha esa base para:
1. Definir formalmente "alumno atrasado" como lógica derivada
2. Proveer rankings de actividades aprobadas
3. Construir los 3 monitores (general, seguimiento, coordinación/admin)

**Restricciones heredadas**:
- Multi-tenancy row-level: todo query filtra por `tenant_id`
- Identidad desde JWT verificado (nunca de parámetros)
- Soft delete en todas las entidades consultadas
- snake_case, Pydantic `extra='forbid'`

## Goals / Non-Goals

**Goals:**
- Definir y exponer lógica de "atrasado" como query derivada (sin stored flag)
- Endpoint de alumnos atrasados con filtros por materia, cohorte, tutor
- Ranking de actividades aprobadas por alumno (window function)
- Reportes por materia: estado de cada actividad, nota actual, estado
- Notas finales agrupadas: promedio por materia, ratio aprobado/total
- Exportar TPs sin corregir (alumnos con actividad esperada pero `nota=null`)
- 3 monitores con scopes diferenciados

**Non-Goals:**
- UI de reportes — solo API REST
- Notificaciones automáticas (futuro C-14)
- Modificación de calificaciones desde estos endpoints
- Cálculo de promedios ponderados

## Decisions

### D1: "Atrasado" es lógica derivada, no stored

**Decisión**: Un alumno está **atrasado** en una actividad cuando:
- La actividad existe en `VersionPadron` (para la `materia_id` y `cohorte_id` del alumno), Y
- NO existe `Calificacion` para ese `(materia_id, usuario_id, asignacion_id)`, O
- Existe `Calificacion` pero `derivar_aprobado(nota, umbral, conjunto_aprobado)` retorna `False`

**Implementación en query**:
```sql
-- Pseudocódigo SQLAlchemy
atrasados = (
    select(EntradaPadron, Asignacion)
    .join(VersionPadron, VersionPadron.id == EntradaPadron.version_padron_id)
    .outerjoin(
        Calificacion,
        and_(
            Calificacion.materia_id == VersionPadron.materia_id,
            Calificacion.usuario_id == EntradaPadron.usuario_id,
            Calificacion.asignacion_id == Asignacion.id,
            Calificacion.deleted_at.is_(None)
        )
    )
    .outerjoin(
        UmbralMateria,
        and_(
            UmbralMateria.materia_id == VersionPadron.materia_id,
            UmbralMateria.asignacion_id == Asignacion.id,
            UmbralMateria.deleted_at.is_(None)
        )
    )
    .where(
        -- condición de atraso
        or_(
            Calificacion.id.is_(None),
            -- derivar_aprobado retorna False
            not_(derivar_aprobado_expression(Calificacion.nota, UmbralMateria))
        )
    )
)
```

**Rationale**: No almacenar `atrasado` evita sincronizar un flag que cambia cuando cambia el umbral o se importa una nueva calificación. La query siempre retorna el estado actual.

**Alternativa considerada**: Store `atrasado` on import and re-derive on threshold change → rejected because it creates stale data windows and extra writes.

### D2: Ranking con window function

**Decisión**: El ranking de alumnos por actividades aprobadas usa:
```sql
ROW_NUMBER() OVER (
    PARTITION BY vp.materia_id
    ORDER BY COUNT(aprobadas) DESC, AVG(nota_numerica) DESC
) as ranking
```

**Rationale**: `ROW_NUMBER` (no `RANK`) para desempate estricto. `COUNT` de aprobadas (no sum de notas) porque la regla de negocio es cantidad de aprobadas, no promedio.

**Alternativa considerada**: `RANK()` para empates → rejected (el desempate por promedio es más informativo).

### D3: 3 monitores con scopes diferenciados

| Monitor | Rol JWT | Scope | Filtros adicionales |
|---------|---------|-------|---------------------|
| General | PROFESOR | Sus materias asignadas | `materia_id IN (materias del profesor)` |
| Seguimiento | TUTOR | Sus tutorados | `usuario_id IN (tutorados del tutor)` |
| Coordinación/Admin | COORDINADOR, ADMIN | Todo el tenant | `fecha_creacion BETWEEN :desde AND :hasta` |

**Rationale**: Cada rol tiene acceso restringido a datos que le conciernen. Coordinator/Admin recibe filtro de fechas para limitar el universo de consulta.

**Implementación**: El servicio recibe `tenant_id` + `usuario_id` del JWT y aplica el scope correspondiente.

### D4: Endpoints — 7 endpoints

| Method | Path | Permiso | Descripción |
|--------|------|---------|-------------|
| `GET` | `/api/analisis/atrasados` | `analisis:ver` | Alumnos atrasados (filtros: materia, cohorte, tutor) |
| `GET` | `/api/analisis/ranking` | `analisis:ver` | Ranking de alumnos por aprobadas (materia) |
| `GET` | `/api/reportes/materia/{materia_id}` | `reportes:ver` | Reporte completo por materia |
| `GET` | `/api/reportes/notas-finales` | `reportes:ver` | Notas finales agrupadas por materia |
| `GET` | `/api/exportacion/tps-sin-corregir` | `reportes:exportar` | Lista de TPs sin nota para re-importación |
| `GET` | `/api/monitores/general` | `analisis:ver` | Monitor general (profesor) |
| `GET` | `/api/monitores/seguimiento` | `analisis:ver` | Monitor seguimiento (tutor) |
| `GET` | `/api/monitores/coordinacion` | `reportes:ver` | Monitor coordinación/admin (rango fechas) |

**Rationale**: Separo `analisis` (queries derivadas), `reportes` (agregaciones), `exportacion` (output para re-import), y `monitores` (vistas pre-armadas por rol).

### D5: Paginación y límites

**Decisión**: Endpoints de lista paginan con `limit` (default 50, max 200) y `offset`. Endpoints de ranking/exportación son `limit` only (cursor-based opcional).

**Rationale**: Evitar queries que retornan miles de filas sin paginar. El ranking por materia usualmente tiene <200 alumnos.

## Data Flow

```
JWT → tenant_id, usuario_id, rol
  ↓
Router valida permiso (require_permission)
  ↓
Service: determina scope según rol
  ↓
Repository: query con tenant_id + scope filters
  ↓
derivar_aprobado() inline en query (no stored)
  ↓
Response DTO (Pydantic, extra='forbid')
```

## Risks / Trade-offs

- **[Risk]** Query con múltiples JOINs y subqueries puede ser lenta en tablas grandes → **Mitigation**: Agregar índice compuesto `(materia_id, usuario_id, deleted_at)` en `calificacion`; particionar por `tenant_id`.
- **[Risk]** `derivar_aprobado` como expresión SQL pura es compleja para tipos mixtos (numérico + texto) → **Mitigation**: Implementar como SQLAlchemy `case()` anidado; para casos complejos usar view materializada refresh on-demand.
- **[Risk]** El monitor de coordinación sin filtro de fechas puede retornar datasets enormes → **Mitigation**: Filtro `desde/hasta` obligatorio con default 30 días; error 400 si rango > 365 días.

## Migration Plan

1. No se requiere migración de DB (no hay modelos nuevos)
2. Crear servicio `AnalisisService` + `ReportesService`
3. Crear repository `AnalisisRepository` con queries derivadas
4. Crear routers `/api/analisis/`, `/api/reportes/`, `/api/exportacion/`, `/api/monitores/`
5. Registrar permisos `analisis:ver`, `reportes:ver`, `reportes:exportar`
6. Tests de integración con DB real
7. Deploy: sin breaking changes

## Open Questions

- **Q1**: ¿El ranking se calcula sobre la versión activa del padrón o todas las versiones? Por ahora sobre la activa; se puede extender con `version_padron_id` como filtro.
- **Q2**: ¿Se incluye `EntradaPadron` con `usuario_id = NULL` (alumno sin cuenta) en los reportes? Sí, se incluyen con `email` como identificador hasta que se registre.