## Context

Este change implementa la gestión de encuentros sincrónicos y guardias (épica 6 del PRD). El proyecto ya cuenta con:

- `C-04` (RBAC): permisos `encuentros:gestionar` y `encuentros:registrar_guardia` seedeados en migración 004, asignados a los roles TUTOR, PROFESOR, COORDINADOR, ADMIN y NEXO según la matriz.
- `C-06` (estructura-academica): modelos `Materia`, `Cohorte` disponibles como FKs.
- `C-07` (usuarios-y-asignaciones): modelo `Usuario` disponible para FK de guardia (`tutor_id`).
- `C-17` (programas-y-fechas): patrón de fragmento LMS (HTML) y router con filtros de query.

La arquitectura sigue Clean Architecture con capas estrictas: Router → Service → Repository → Model. No se crea modelo `Dictado` (ADR-006 dice que viene después); las FKs apuntan directamente a `materia` y `cohorte`.

## Goals / Non-Goals

**Goals:**
- Modelar `SlotEncuentro` como plantilla recurrente semanal con generación automática de `InstanciaEncuentro` (RN-13: `fecha_inicio + (semana * 7 días)`).
- Permitir encuentros únicos (`slot_id = NULL` en `InstanciaEncuentro`).
- Editar instancias individuales: estado, meet_url, video_url, comentario.
- Listar encuentros con filtros (materia, cohorte, estado, rango de fechas).
- Generar fragmento HTML para incrustar en aula virtual (F6.4).
- CRUD de guardias con scope: TUTOR ve/edita las propias; COORDINADOR/ADMIN ven todas.
- Export de guardias a CSV con módulo `csv` de stdlib.

**Non-Goals:**
- No integración con Zoom/Meet/Teams API — las URLs son texto libre.
- No control de asistencia ni tracking de participantes.
- No notificaciones automáticas al crear/modificar encuentros.
- No modelo `Dictado` — ADR-006 pospone esa entidad. Las FKs son directas a `materia` y `cohorte`.
- No hard-delete — soft delete siempre.

## Decisions

### D1: Un servicio unificado para encuentros (`EncuentrosService`)

**Decisión**: Un solo service que maneja tanto `SlotEncuentro` como `InstanciaEncuentro`, porque la generación de instancias desde el slot es una operación atómica que cruza ambas tablas.

**Alternativa considerada**: Dos services separados con coordinación en el router. Rechazada porque la atomicidad del create (slot + instancias en una transacción) es más natural en un service único.

### D2: Guardia como service separado (`GuardiaService`)

**Decisión**: Service independiente porque `Guardia` no comparte lógica transaccional con `SlotEncuentro`/`InstanciaEncuentro`. Su scope de autorización es distinto (TUTOR solo ve las propias).

### D3: Generación de instancias con date arithmetic

**Decisión**: Loop en Python: `fecha_inicio + timedelta(weeks=i)` para `i` en `range(cant_semanas)`. Sin stored procedures ni SQL complejo.

**Alternativa considerada**: `generate_series` en PostgreSQL. Rechazada porque la generación de UUIDs y la inserción de filas completas es más legible y testeable en Python.

**Riesgo mitigado**: `cant_semanas` se valida con un máximo razonable (ej. 52, un año de encuentros semanales) para evitar generación descontrolada.

### D4: Fragmento HTML con string formatting

**Decisión**: Generar HTML con f-strings, siguiendo el patrón de `generar_fragmento_lms` en `ProgramaFechasService` (C-17). Sin template engine.

**Alternativa considerada**: Jinja2. Rechazada por overkill para un fragmento simple; el patrón ya establecido en C-17 usa strings.

### D5: Export CSV con `csv.DictWriter`

**Decisión**: Usar `csv.DictWriter` de stdlib. El endpoint devuelve `StreamingResponse` con `Content-Type: text/csv`.

### D6: Permisos ya seedeados — no se requiere nueva migración de seed

**Verificación**: La migración 004 (`004_rbac_tables.py`) ya incluye `encuentros:gestionar` (línea 191: ID `00000000-0000-0000-0001-a00000000010`) y `encuentros:registrar_guardia` (línea 192: ID `00000000-0000-0000-0001-a00000000011`). Ambos están asignados a TUTOR, PROFESOR, COORDINADOR y ADMIN en la matriz `rol_permiso`. No se requiere seed adicional.

### D7: Encuentro único como endpoint separado

**Decisión**: `POST /api/encuentros/instancias/unico` crea una `InstanciaEncuentro` con `slot_id=NULL` directamente. No requiere `SlotEncuentro` previo.

**Alternativa considerada**: Un solo endpoint que infiera el tipo según la presencia de `cant_semanas`. Rechazada porque complica la validación y la semántica del response.

### D8: Scope de guardia por rol

| Rol | Scope |
|-----|-------|
| TUTOR | Solo ve/edita guardias donde `tutor_id == current_user.user_id` |
| COORDINADOR, ADMIN | Ven todas las guardias del tenant |
| Otros roles | Sin acceso (403 por falta de permiso) |

## Risks / Trade-offs

- **[Riesgo] Zona horaria en cálculo de fechas**: `datetime.date` + `timedelta(weeks=n)` no tiene zona horaria. Las fechas se almacenan como `DATE` (sin tz). Si el servidor y el cliente están en zonas distintas, la fecha del encuentro podría interpretarse diferente. → **Mitigación**: Usar `datetime.date` puro sin conversión tz. Las fechas son "día calendario", no instantes UTC. Documentar que la interpretación es local al tenant.

- **[Riesgo] `cant_semanas` grande**: Un slot con `cant_semanas=500` generaría 500 inserts en una transacción. → **Mitigación**: Validar `cant_semanas` entre 1 y 52 (máximo un año). Si el negocio requiere más, se puede aumentar o paginar.

- **[Trade-off] Sin cascade delete entre slot e instancias**: Si se soft-deletea un `SlotEncuentro`, las instancias ya generadas se preservan (consistencia histórica). → **Mitigación**: El listado de instancias solo muestra las no deleted; si el slot padre fue deleted, el `slot_id` queda como FK huérfana lógica (aceptable para trazabilidad).

## Open Questions

Ninguna. Los permisos están seedeados, las FK existen, los patrones están establecidos.
