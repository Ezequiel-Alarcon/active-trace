## Why

El equipo docente necesita un sistema de tareas internas para gestionar el workflow de pendientes entre coordinación y docentes: asignar actividades, hacer seguimiento, agregar comentarios y cerrar el ciclo. Sin esto, el seguimiento es manual (WhatsApp, email) sin trazabilidad. Es un módulo de alto uso (cientos de tareas simultáneas) que requiere filtrado eficiente por contexto académico.

## What Changes

- Nuevos modelos `Tarea` y `ComentarioTarea` con herencia `TenantScopedMixin`, soft-delete, migración `019_tareas.py`
- CRUD completo de tareas con scope: PROFESOR ve/modifica solo las propias; COORDINADOR/ADMIN ven todas
- Endpoints de comentarios (hilo) asociados a una tarea
- Vista "Mis tareas" filtrada por estado, materia, búsqueda libre
- Vista de administración con filtros por docente, materia, estado

## Capabilities

### New Capabilities
- `tareas-crud`: Creación, lectura, actualización de estado y soft-delete de Tarea. Permiso `tareas:gestionar` con scope `(propio)` para PROFESOR, `(todo)` para COORDINADOR/ADMIN.
- `tareas-comentarios`: CRUD de comentarios en hilo por tarea. Permiso `tareas:gestionar` con el mismo scope.
- `tareas-visibilidad`: Listados filtrados ("Mis tareas" para el asignado, "Todas las tareas" para coordinación) con paginación, filtros por estado/materia/docente y búsqueda libre.

### Modified Capabilities
*(ninguna — no se modifican capacidades existentes)*

## Impact

- **backend/app/models/tarea.py** — nuevo modelo `Tarea`, `ComentarioTarea`
- **backend/app/models/__init__.py** — importar modelos (si no hay circular import)
- **backend/app/schemas/tareas.py** — schemas Create, Update, Response, ListResponse
- **backend/app/repositories/tareas.py** — `TareaRepository` extendiendo `TenantScopedRepository`
- **backend/app/services/tareas.py** — `TareaService` con lógica de scope y negocio
- **backend/app/routers/tareas.py** — endpoints REST con `require_permission("tareas:gestionar")`
- **backend/app/api/v1/main_router.py** — montar router
- **backend/alembic/versions/019_tareas.py** — migración
- **backend/tests/tareas/** — tests unitarios y de integración
- Nuevo permiso: `tareas:gestionar` en el catálogo RBAC
