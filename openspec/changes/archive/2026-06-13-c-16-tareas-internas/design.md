## Context

C-16 agrega el módulo de Tareas Internas (Épica 8) para gestionar el workflow de pendientes entre coordinación y docentes. Es un módulo CRUD con lógica de scope por rol: PROFESOR solo ve tareas donde es `asignado_a`; COORDINADOR/ADMIN ven todas. Incluye hilo de comentarios. El modelo sigue el patrón `TenantScopedMixin` (soft-delete, tenant isolation row-level). Es un módulo de alta concurrencia (cientos de tareas simultáneas).

## Goals / Non-Goals

**Goals:**
- ABM completo de `Tarea` con estado workflow: Pendiente → En progreso → Resuelta, y Cancelada
- Hilo de comentarios por tarea (`ComentarioTarea`)
- Scope de visibilidad: PROFESOR ve/modifica solo las propias; COORDINADOR/ADMIN ven todas
- Listados paginados con filtros por estado, materia, docente asignado, búsqueda libre
- Permiso `tareas:gestionar` en el catálogo RBAC

**Non-Goals:**
- Notificaciones push/email al asignar tarea (futura iteración)
- Delegación/escalamiento automático (la delegación es manual por ahora)
- Integración con calendario o eventos

## Decisions

### D1 — Scope de visibilidad desde el repository, no desde el service
En lugar de usar dos repositories separados, `TareaRepository` recibe un `user_id` opcional. Si se pasa, agrega `WHERE asignado_a = user_id`. Esto mantiene la lógica de scope en la capa de datos.

### D2 — Un solo permiso `tareas:gestionar` con scope aplicado en código
No se crean permisos separados por rol. El permiso `tareas:gestionar` se asigna a PROFESOR, COORDINADOR y ADMIN. El scope `(propio)` vs `(todo)` se resuelve en el service comparando el rol del usuario autenticado. Esto mantiene simple el catálogo de permisos.

### D3 — ComentarioTarea como modelo separado (no JSONB)
Se modela como tabla independiente con FK a Tarea. Permite queries eficientes (`ORDER BY creado_at`), paginación de comentarios, y auditoría granular. No hay ventaja real en usar JSONB para un hilo que se consulta frecuentemente.

### D4 — Sin endpoints separados de comentarios; van anidados a la tarea
Los comentarios se crean/listan a través de la tarea: `POST /api/tareas/{id}/comentarios`, `GET /api/tareas/{id}/comentarios`. Esto mantiene la cohesión del recurso.

### D5 — Migración única `019_tareas.py`
Una sola migración Alembic que crea ambas tablas (Tarea, ComentarioTarea) y sus índices.

## Risks / Trade-offs

- [Alta concurrencia] Varios docentes pueden actualizar el estado de una tarea simultáneamente. → Confiar en row-level locking de PostgreSQL; la transacción corta (flush) minimiza riesgo de race conditions. No se requiere optimistic locking en la primera versión.
- [Scope por rol] Si un COORDINADOR es también PROFESOR en otro contexto, podría ver tareas que no debería. → El rol evaluado es el del JWT (no hay multi-rol por sesión en la versión actual). Asumimos que un usuario tiene un rol dominante.
- [Crecimiento de comentarios] Tareas con cientos de comentarios pueden degradar performance. → Paginación obligatoria en el listado de comentarios (max 50 por página).
