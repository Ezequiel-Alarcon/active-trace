## Context

C-07 (usuarios-y-asignaciones) implementa el modelo `Asignacion` (usuario_id, rol_id, contexto_tipo, contexto_id, responsable_id, desde, hasta) con CRUD individual vía `AsignacionService`. El permiso `equipos:asignar` ya existe y está asignado a COORDINADOR y ADMIN en el seeder de RBAC. Los endpoints actuales en `/api/asignaciones` cubren operaciones individuales.

C-08 agrega operaciones batch sobre el mismo modelo (`Asignacion`) sin tocar su schema. Son operaciones de coordinación académica que el COORDINADOR ejecuta en el flujo FL-03 (setup de cuatrimestre): clonar equipos del período anterior, ajustar vigencias, asignar docentes en masa, revisar composición del equipo y exportar.

**Restricciones heredadas**:
- Soft delete siempre (no hard delete)
- Multi-tenant row-level: cada asignación tiene `tenant_id`
- RBAC: `equipos:asignar` requerido en todos los endpoints de escritura
- Identidad desde JWT (nunca desde parámetros)
- snake_case en Python, extra='forbid' en Pydantic
- Consultas solo vía repositories, lógica de negocio en services, nunca en routers

## Goals / Non-Goals

**Goals:**
- Endpoint `GET /api/equipos/mis-equipos` para consulta de asignaciones propias del usuario autenticado
- Endpoint `POST /api/equipos/asignacion-masiva` para creación batch de asignaciones
- Endpoint `POST /api/equipos/clonar` para duplicar asignaciones entre cohortes
- Endpoint `PATCH /api/equipos/vigencia` para modificar fechas en bloque
- Endpoint `GET /api/equipos/exportar` para descarga CSV del equipo
- Action code `ASIGNACION_MODIFICAR` en el vocabulario de auditoría
- Tests: clonado entre cohortes, asignación masiva, modificación de vigencia en bloque, export

**Non-Goals:**
- No modifica el modelo `Asignacion` ni su tabla
- No crea nuevas migraciones (opera sobre tablas de C-07)
- No cambia el CRUD individual de asignaciones (ya funciona en C-07)
- No implementa validación de solapamiento de asignaciones (fuera de scope)
- No notifica a docentes sobre nuevas asignaciones (C-13, C-14)
- No modifica el frontend (C-23)

## Decisions

### D1: Service dedicado `EquipoService` en archivo separado
**Decisión**: Crear `app/services/equipos.py` con `EquipoService`, en lugar de extender `AsignacionService`.
**Razón**: `AsignacionService` ya tiene 371 líneas con CRUD individual. Agregar operaciones batch lo llevaría a ~600+ LOC, violando la regla dura de ≤500 LOC por archivo. Separar por responsabilidad (individual vs batch) respeta SRP y mantiene testabilidad.
**Alternativa considerada**: Extender `AsignacionService`. Rechazada porque mezcla dos responsabilidades distintas y rompe el límite de LOC.

### D2: Asignación masiva no transaccional con reporte parcial
**Decisión**: Cada asignación del lote se crea individualmente con su propia validación. Si una falla (usuario duplicado, entidad inexistente), se registra el error y se continúa con las siguientes. La respuesta incluye listas de `creadas` y `fallidas`.
**Razón**: El dominio requiere lote no atómico (ver task description: "el lote no es atómico — se informa cuáles fallaron"). Una transacción global complicaría el rollback y haría imposible el reporte parcial.
**Alternativa considerada**: Transacción global con rollback. Rechazada porque el requerimiento explícito pide procesamiento parcial con informe de fallidas.

### D3: Clonado con rollback manual, no transacción global
**Decisión**: Clonar itera sobre asignaciones vigentes de la cohorte origen y crea una a una en destino. Si una asignación ya existe (mismo usuario+rol+contexto), se omite (no se duplica). Si ocurre un error inesperado, se hace soft-delete de las ya creadas en este lote (rollback manual).
**Razón**: Son potencialmente muchas rows. Una transacción global con isolation level serializable sobre tantas filas impactaría el rendimiento. El rollback manual es aceptable porque el clonado es una operación poco frecuente (una vez por cuatrimestre).
**Alternativa considerada**: Transacción global. Rechazada por performance y porque el dominio ya acepta procesamiento por asignación.

### D4: Export en CSV con módulo `csv` de stdlib
**Decisión**: Usar el módulo `csv` de la stdlib para generar CSV. Devolver `StreamingResponse` con `text/csv` MIME type.
**Razón**: La task explícitamente dice "formato CSV con `csv` module de stdlib, no dependencia externa". Mantiene el proyecto sin dependencias innecesarias.
**Alternativa considerada**: openpyxl para Excel o pandas. Rechazada por agregar dependencias innecesarias para un requerimiento simple.

### D5: Vigencia general filtra solo asignaciones vigentes
**Decisión**: El endpoint de modificación de vigencia (`PATCH /api/equipos/vigencia`) solo afecta asignaciones cuyo `estado_vigencia == "Vigente"`. Las vencidas no se modifican. Esto es explícito del requerimiento F4.6.
**Razón**: Una asignación vencida ya cumplió su ciclo. Modificarla podría reactivar inadvertidamente una relación que ya terminó.

### D6: Action code `ASIGNACION_MODIFICAR` en auditoría
**Decisión**: Agregar `ASIGNACION_MODIFICAR` al vocabulario de `app/core/audit.py` y emitirlo en operaciones batch (masiva, clonar, vigencia). El CRUD individual ya emite eventos de repo (create/update/soft_delete); los endpoints batch emiten un evento adicional a nivel de operación.
**Razón**: Trazabilidad — permite distinguir "se modificó una asignación individual" de "se ejecutó una operación batch sobre el equipo".

### D7: Schemas en `app/schemas/equipos.py`
**Decisión**: Crear archivo separado de schemas, no extender `app/schemas/usuarios.py`.
**Razón**: Los schemas de equipos tienen formas distintas (listas de resultados batch, filtros de vigencia, payloads de clonado). Mantenerlos separados respeta el límite de LOC y el principio de segregación.

## Risks / Trade-offs

- **[Riesgo] Clonado parcialmente fallido deja asignaciones huérfanas en destino** → Rollback manual con soft-delete de las creadas en el lote. El endpoint devuelve cuáles se crearon y cuáles fallaron, permitiendo al coordinador decidir.
- **[Riesgo] Asignación masiva con muchos usuarios (100+) puede ser lenta** → Cada asignación valida usuario, rol y contexto individualmente con queries separadas. Para lotes grandes (>100) considerar en el futuro un endpoint async con background job.
- **[Riesgo] Export CSV con muchos registros carga en memoria** → Si el equipo tiene cientos de docentes, usar `StreamingResponse` con generator para no materializar toda la respuesta en memoria.
- **[Trade-off] Sin validación de solapamiento** → Dos asignaciones para el mismo usuario+rol+contexto con fechas solapadas son técnicamente posibles. El dominio actual no lo requiere, pero podría agregarse en futuro como regla de negocio adicional.
- **[Trade-off] Email descifrado en export** → El CSV contiene el email en texto plano porque el coordinador necesita contactar al equipo. El endpoint está protegido por `equipos:asignar` (COORDINADOR/ADMIN), que ya tiene acceso a datos del usuario vía otros endpoints.

## Migration Plan

1. Desplegar nuevo código (nuevos archivos: service, router, schemas; modificación: audit.py, main_router.py)
2. No requiere migración de base de datos
3. No requiere backfill de datos
4. Rollback: revertir commit (los endpoints son aditivos, no modifican comportamiento existente)

## Open Questions

- **OQ-01**: ¿El endpoint `mis-equipos` debe devolver datos expandidos del usuario (nombre, apellido, email) o solo los IDs de asignación? → Se asume expandido porque el docente necesita ver nombres de materias/carreras, no solo IDs. Confirmar con stakeholders.
- **OQ-02**: ¿CSV con BOM para Excel en Windows? → Se asume UTF-8 con BOM (`\ufeff`) para compatibilidad con Excel.
