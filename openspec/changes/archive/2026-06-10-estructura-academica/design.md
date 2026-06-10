## Context

C-06 es el primer change del módulo académico. Las entidades Carrera, Cohorte y Materia son la base sobre la que operarán: importación de calificaciones (C-07), detección de atrasos (C-09), comunicación masiva (C-10), y la instancia de dictado (C-07 o posterior).

El change depende de C-04 (RBAC con permisos finos), que ya seedeó el permiso `estructura:gestionar` y lo asignó al rol ADMIN. No requiere nuevas migraciones de RBAC ni seeds.

El proyecto sigue Clean Architecture con flujo unidireccional: Router → Service → Repository → Model. La capa de repositorios ya tiene `TenantScopedRepository[T]` con CRUD genérico, soft delete y scoping automático por tenant. La factory `get_tenant_repository(model, session)` obtiene el tenant del `TenantContext`.

## Goals / Non-Goals

**Goals:**
- ABM completo de Carrera, Cohorte y Materia con scoping multi-tenant automático.
- Validación de reglas de negocio: unicidad por tenant, carrera activa para cohortes, soft delete.
- Endpoints REST bajo `/api/admin` con guard `estructura:gestionar`.
- Migración 005 que crea las tres tablas con índices de unicidad compuestos por `(tenant_id, ...)`.
- Tests que cubren CRUD, unicidad, aislamiento y validaciones de negocio.

**Non-Goals:**
- Instancia de dictado (Materia × Carrera × Cohorte). Eso es C-07 o posterior. ADR-006 cerrado: Materia es el catálogo, Dictado viene después.
- Asignación de docentes a cohortes. Viene en C-13 (equipos docentes).
- Relación Cohorte ↔ Moodle. Viene en C-07 (integración Moodle).
- Endpoints de consulta pública. Solo ADMIN puede gestionar estructura en este change.

## Decisions

### D1: Modelos — TenantScopedMixin como base

Los tres modelos (`Carrera`, `Cohorte`, `Materia`) heredan de `TenantScopedMixin`, que provee `id` (UUID), `tenant_id`, `created_at`, `updated_at`, `deleted_at`. Esto garantiza soft delete y tenant scoping por construcción.

Cada modelo declara sus propios `__table_args__` con `Index("ix_<tabla>_tenant", "tenant_id")` y `Index("ix_<tabla>_tenant_deleted", "tenant_id", "deleted_at")`, siguiendo el patrón del mixin.

**Alternativa considerada**: crear un mixin `EstructuraMixin` con campos comunes (estado, codigo). Descartado: las tres entidades tienen constraints de unicidad diferentes y campos específicos (Cohorte tiene FK a Carrera, fechas de vigencia, etc.). Un mixin unificaría campos que no son realmente compartidos.

### D2: Enums de estado — Python Enum mapeado a SAEnum

Cada modelo usa un `enum.Enum` de Python (`CarreraEstado`, `CohorteEstado`, `MateriaEstado`) con valores `Activa`/`Inactiva`. Se mapea a `SAEnum` con `values_callable` y un `CheckConstraint` en la tabla.

Sigue el patrón de `TenantEstado` en `app/models/tenant.py`.

**Alternativa considerada**: boolean `activa`. Descartado porque el dominio ya usa enums (tenant, RBAC) y puede necesitar estados adicionales en el futuro (ej. "EnTransicion", "Suspendida"). Un enum es más extensible.

### D3: Unicidad compuesta por tenant

Las constraints de unicidad son compuestas con `tenant_id`:
- Carrera: `(tenant_id, codigo)`
- Cohorte: `(tenant_id, carrera_id, nombre)`
- Materia: `(tenant_id, codigo)`

Esto permite que dos tenants tengan una carrera con el mismo código — cada tenant es un universo aislado.

La validación de unicidad en el servicio se hace consultando al repositorio con filtros por tenant, no con `try/except IntegrityError`. La constraint en DB es la última línea de defensa; la validación en servicio da mensajes de error claros (409 con detalle en español).

### D4: Cohorte → Carrera FK con validación en servicio

`Cohorte.carrera_id` tiene FK a `Carrera.id` con `ON DELETE RESTRICT`. La lógica de "carrera inactiva no admite cohortes abiertas" se implementa en el servicio: antes de crear o activar una cohorte, se verifica que `carrera.estado == Activa`. Si está inactiva, se rechaza con 422.

**Alternativa considerada**: trigger en DB. Descartado: la lógica de negocio vive en el servicio, no en la DB. Un trigger haría el sistema más difícil de testear y debuggear.

### D5: Repositorio — TenantScopedRepository sin subclase

A diferencia de C-04 (que creó `RolRepository`, `PermisoRepository`, etc. con queries especializadas), usamos `TenantScopedRepository` directamente con la factory `get_tenant_repository(model, session)`. Las validaciones de negocio (unicidad, carrera activa) viven en el servicio.

**Alternativa considerada**: `EstructuraRepository` con métodos `get_by_codigo`, `get_cohortes_by_carrera`. Descartado por simplicidad: `TenantScopedRepository.list()` acepta filtros `(Model.codigo == value,)` que cubren todos los casos. Si en changes futuros se necesitan queries complejas (JOINs, agregaciones), se creará la subclase en ese momento.

### D6: Router — un solo archivo con tres grupos de endpoints

Un único router `app/routers/estructura.py` con `APIRouter(prefix="/api/admin", tags=["admin", "estructura"])` agrupa los endpoints de carreras, cohortes y materias. Cada grupo tiene su propio `PERM = "estructura:gestionar"` (mismo permiso para los tres).

**Alternativa considerada**: tres routers separados (`carreras.py`, `cohortes.py`, `materias.py`). Descartado: comparten el mismo prefijo, permiso, dependencias y patrón. Tres archivos duplicarían boilerplate sin beneficio.

## Risks / Trade-offs

- **[R1] FK Cohorte → Carrera bloquea el borrado de carreras con cohortes**: El soft delete mitiga esto parcialmente (no se borran carreras, se desactivan), pero si se necesita borrar físicamente una carrera, hay que quitar cohortes primero. → Mitigación: soft delete es la norma; el hard delete solo existe vía `unsafe_physical_delete` y nunca se usa desde la API.
- **[R2] Sin repositorio especializado, queries complejas futuras requerirán refactor**: Si C-07 o C-09 necesitan queries con JOINs entre Carrera, Cohorte y Materia, habrá que extraer un `EstructuraRepository`. → Mitigación: refactor previsto y de bajo impacto; el servicio llama al repo genérico por ahora.
- **[R3] Cohorte con `vig_hasta = NULL` significa "abierta"**: No hay validación de que `vig_hasta >= vig_desde` cuando no es NULL. → Mitigación: se agrega validación en el servicio al crear/editar cohorte.
