## 1. Modelos y Migración

- [x] 1.1 Crear `backend/app/models/tarea.py` con modelos `Tarea` (TenantScopedMixin), `EstadoTarea` enum y `ComentarioTarea` (TenantScopedMixin)
- [x] 1.2 Agregar import de modelos en `backend/app/models/__init__.py` (verificar circular imports como avisos)
- [x] 1.3 Generar migración `backend/alembic/versions/019_tareas.py` con ambas tablas, índices y FK

## 2. Schemas Pydantic

- [x] 2.1 Crear `backend/app/schemas/tareas.py` con `TareaCreate`, `TareaUpdate`, `TareaResponse`, `TareaListResponse`, `ComentarioCreate`, `ComentarioResponse`, `ComentarioListResponse` (todos con `extra='forbid'`)

## 3. Repository

- [x] 3.1 Crear `backend/app/repositories/tareas.py` con `TareaRepository(TenantScopedRepository[Tarea])` incluyendo métodos: `list_by_asignado`, `list_all_filtered` con filtros dinámicos

## 4. Service

- [x] 4.1 Crear `backend/app/services/tareas.py` con `TareaService` incluyendo: CRUD con scope (propio vs todo), transiciones de estado validadas, manejo de comentarios

## 5. Router

- [x] 5.1 Crear `backend/app/routers/tareas.py` con endpoints: `POST/GET/PATCH/DELETE /api/tareas`, `GET /api/tareas/mis-tareas`, `POST/GET /api/tareas/{id}/comentarios`, todos con `require_permission("tareas:gestionar")`
- [x] 5.2 Montar router en `backend/app/api/v1/main_router.py`

## 6. Permisos RBAC

- [x] 6.1 Agregar permiso `tareas:gestionar` al catálogo de permisos (asignar a PROFESOR, COORDINADOR, ADMIN) en migración 019

## 7. Tests

- [x] 7.1 Crear `backend/tests/tareas/conftest.py` con fixtures de Tarea y ComentarioTarea
- [x] 7.2 Escribir tests de CRUD (crear, leer, actualizar estado, soft-delete) con scope PROFESOR vs COORDINADOR
- [x] 7.3 Escribir tests de comentarios (crear, listar, scope)
- [x] 7.4 Escribir tests de visibilidad (mis-tareas, listado admin, filtros)
- [x] 7.5 Escribir tests de transiciones de estado inválidas
