## Context

C-17 introduce dos entidades del dominio académico: `ProgramaMateria` (documento por materia × carrera × cohorte) y `FechaAcademica` (fechas de parciales, TP y coloquios por materia × cohorte × número). Son la base para que docentes y coordinadores organicen la vida académica de cada materia dentro de una cohorte y generen contenido para el LMS (F5.3, F5.4).

El change depende de C-06 (estructura-academica), que ya provee los modelos `Carrera`, `Cohorte` y `Materia` con sus repositorios y servicios. El permiso `estructura:gestionar` ya está seedeado y asignado a ADMIN y COORDINADOR.

El proyecto sigue Clean Architecture con flujo unidireccional: Router → Service → Repository → Model. La capa de repositorios ya tiene `TenantScopedRepository[T]` con CRUD genérico, soft delete y scoping automático por tenant.

## Goals / Non-Goals

**Goals:**
- ABM completo de `ProgramaMateria` con unicidad `(tenant_id, materia_id, carrera_id, cohorte_id)`.
- ABM completo de `FechaAcademica` con unicidad `(tenant_id, materia_id, cohorte_id, tipo, numero_instancia)`.
- `referencia_archivo` de ProgramaMateria es opaca — el sistema solo almacena y devuelve la string, no interpreta contenido ni gestiona archivos físicos.
- Endpoint `GET /api/fechas-academicas/fragmento-lms` que devuelve HTML formateado con fechas agrupadas por materia y tipo, listo para copiar al aula virtual.
- Migración 007 que crea las dos tablas con índices de unicidad compuestos y FKs a las entidades de C-06.
- Tests que cubren CRUD, unicidad, aislamiento multi-tenant, fragmento LMS y validaciones de negocio.

**Non-Goals:**
- Upload físico de archivos. `referencia_archivo` es una string; el almacenamiento real (S3, disco local) se implementa en un change futuro de gestión de archivos.
- Integración automática con Moodle. El fragmento LMS es contenido para copiar/pegar manualmente. La push automática al LMS es C-10 o posterior.
- Entidad `Dictado`. ADR-006 establece que `Dictado` (Materia × Carrera × Cohorte) viene en otro change. `ProgramaMateria` usa directamente la combinación materia + carrera + cohorte.
- Notificaciones automáticas sobre fechas. Eso pertenece a C-10 (comunicación masiva).
- Listado tipo calendario en frontend. El backend provee los datos; el frontend los renderiza en C-21 o posterior.

## Decisions

### D1: Modelos — TenantScopedMixin con FKs a estructura

Ambos modelos (`ProgramaMateria`, `FechaAcademica`) heredan de `TenantScopedMixin`, que provee `id` (UUID), `tenant_id`, `created_at`, `updated_at`, `deleted_at`. Esto garantiza soft delete y tenant scoping por construcción.

Cada modelo declara sus propios `__table_args__` con `Index("ix_<tabla>_tenant", "tenant_id")` e `Index("ix_<tabla>_tenant_deleted", "tenant_id", "deleted_at")`, más los índices de unicidad compuestos.

**Alternativa considerada**: crear una entidad intermedia `Dictado` y asociar `ProgramaMateria` y `FechaAcademica` a ella. Descartado por ADR-006: `Dictado` viene en otro change. La combinación materia + carrera + cohorte es suficiente para la unicidad. Cuando `Dictado` exista, se podrá migrar sin breaking changes (FK opcional adicional).

### D2: Enum `TipoFechaAcademica` — Parcial, TP, Coloquio

El modelo `FechaAcademica` usa un `enum.Enum` de Python (`TipoFechaAcademica`) con valores `Parcial`, `TP`, `Coloquio`. Se mapea a `SAEnum` con `values_callable`. Sigue el patrón de `CarreraEstado`, `CohorteEstado`, `MateriaEstado`.

**Alternativa considerada**: string libre. Descartado: el dominio define tres tipos concretos; un enum previene typos y facilita filtros y agrupamientos en el fragmento LMS.

### D3: Unicidad compuesta por tenant para cada entidad

- `ProgramaMateria`: unicidad `(tenant_id, materia_id, carrera_id, cohorte_id)` — un solo programa por combinación materia × carrera × cohorte.
- `FechaAcademica`: unicidad `(tenant_id, materia_id, cohorte_id, tipo, numero_instancia)` — no puede haber dos "Parcial 1" para la misma materia y cohorte.

La validación de unicidad en el servicio se hace consultando al repositorio con filtros (no `try/except IntegrityError`). La constraint en DB es la última línea de defensa.

### D4: `referencia_archivo` como string opaca

El campo `referencia_archivo` de `ProgramaMateria` es un `String(512)` que almacena una ruta o URL. El sistema no valida que el archivo exista ni interpreta su contenido. El frontend recibe este valor y lo usa para construir links de descarga cuando exista un servicio de archivos.

Esto es intencional: la gestión de archivos físicos (upload, storage, serving) es un dominio separado que se implementa en un change futuro. Hoy, el valor se puede setear manualmente o mockear en tests.

**Alternativa considerada**: implementar upload de archivos con FastAPI `UploadFile`. Descartado: agrega complejidad de storage (S3/local) y CDN que no pertenece a este change. El scope es el modelo de datos y CRUD de la referencia.

### D5: Repositorio — TenantScopedRepository sin subclase

Siguiendo el patrón de C-06, usamos `TenantScopedRepository` directamente con la factory `get_tenant_repository(model, session)`. Las validaciones de negocio (unicidad, existencia de FKs) viven en el servicio.

No se crea un repositorio especializado porque las queries necesarias (list con filtros por materia, cohorte, carrera, tipo) se cubren con el método `list(filters=[...])` genérico.

**Alternativa considerada**: `ProgramaFechasRepository` con métodos como `get_by_materia_cohorte`. Descartado: el repo genérico es suficiente. Si se necesitan queries complejas en el futuro (JOINs para el fragmento LMS con datos de materia/carrera), se creará la subclase en ese momento.

### D6: Router — un solo archivo con prefijo `/api`

Un único router `app/routers/programas_fechas.py` con `APIRouter(prefix="/api", tags=["programas", "fechas"])` agrupa los endpoints de programas y fechas. Ambos usan el mismo permiso `estructura:gestionar`.

El endpoint de fragmento LMS se monta bajo `/api/fechas-academicas/fragmento-lms` porque opera sobre el mismo recurso.

**Alternativa considerada**: dos routers separados (`programas.py`, `fechas.py`). Descartado: comparten el mismo permiso, patrón de dependencias y servicio (`ProgramaFechasService`). Un solo archivo evita duplicación de boilerplate.

### D7: Fragmento LMS — HTML server-side sin template engine

El endpoint `GET /api/fechas-academicas/fragmento-lms` genera HTML simple con las fechas agrupadas por materia y tipo. No usa Jinja2 ni otro template engine — es formateo de strings en el servicio. El HTML es mínimo: una tabla o lista con materia, tipo, número, fecha, título y descripción.

Parámetros de query:
- `materia_id` (requerido): para qué materia generar el fragmento
- `cohorte_id` (requerido): para qué cohorte

**Alternativa considerada**: generar el fragmento en el frontend con los datos del endpoint de listado. Descartado: F5.4 pide explícitamente un endpoint que devuelva contenido listo para el LMS. El backend es el source of truth del formato.

### D8: Migración 007 — dos tablas en una migración

Una sola migración `007_programas_fechas` crea ambas tablas (`programa_materia`, `fecha_academica`). Esto sigue el principio de "una migración por change". La down revision apunta a `006_usuarios_asignaciones` (C-07). Si C-07 no existe aún, la migración se crea con un placeholder y se ajusta cuando C-07 se complete.

**Alternativa considerada**: dos migraciones separadas (007 para programas, 008 para fechas). Descartado: ambas entidades pertenecen al mismo change; separarlas complica el rollback y no aporta granularidad útil.

## Risks / Trade-offs

- **[R1] `referencia_archivo` puede apuntar a recursos inexistentes**: Si el valor se setea manualmente y el archivo no existe, el frontend mostrará un link roto. → Mitigación: el campo es opaco por diseño. Un change futuro de gestión de archivos agregará validación y upload real.
- **[R2] Sin `Dictado`, la unicidad de ProgramaMateria podría cambiar**: Si `Dictado` introduce una FK adicional, el índice de unicidad actual `(tenant_id, materia_id, carrera_id, cohorte_id)` podría necesitar ajuste. → Mitigación: la migración de `Dictado` podrá alterar el índice sin pérdida de datos porque la combinación materia + carrera + cohorte está incluida en la futura FK a `Dictado`.
- **[R3] Fragmento LMS sin i18n**: El HTML generado está en español fijo. Si se necesita multi-idioma en el futuro, habrá que refactorizar. → Mitigación: el scope actual es single-tenant en español. La i18n se agrega cuando sea necesaria sin cambiar la forma del endpoint.
- **[R4] Performance del fragmento LMS con muchas fechas**: Si una materia tiene 50+ fechas, el HTML generado puede ser grande. → Mitigación: el endpoint acepta `materia_id` y `cohorte_id` como filtros obligatorios, limitando el scope. Para una materia típica hay 4-8 fechas. Bajo riesgo.
