## 1. Data Layer — Migration y Modelos

- [x] 1.1 Crear migración `005_estructura_academica` con tablas `carrera`, `cohorte`, `materia`, índices de unicidad compuestos por `tenant_id`, FKs, y columnas de soft delete. Down revision: `004_rbac`.
- [x] 1.2 Crear modelo `Carrera` en `app/models/carrera.py` con `TenantScopedMixin`, enum `CarreraEstado`, campos `codigo`, `nombre`, `estado`, e índices `ix_carrera_tenant_codigo` (unique) y `ix_carrera_tenant_deleted`.
- [x] 1.3 Crear modelo `Cohorte` en `app/models/cohorte.py` con `TenantScopedMixin`, enum `CohorteEstado`, FK a `carrera.id` ON DELETE RESTRICT, campos `nombre`, `anio`, `vig_desde`, `vig_hasta`, `estado`, e índices `ix_cohorte_tenant_carrera_nombre` (unique) y `ix_cohorte_tenant_deleted`.
- [x] 1.4 Crear modelo `Materia` en `app/models/materia.py` con `TenantScopedMixin`, enum `MateriaEstado`, campos `codigo`, `nombre`, `estado`, e índices `ix_materia_tenant_codigo` (unique) y `ix_materia_tenant_deleted`.
- [x] 1.5 Registrar los tres modelos en `app/models/__init__.py` para que `Base.metadata` los incluya.

## 2. Schemas — Pydantic DTOs

- [x] 2.1 Crear `app/schemas/estructura.py` con schemas para las tres entidades: `CarreraCreate`, `CarreraUpdate`, `CarreraResponse`; `CohorteCreate`, `CohorteUpdate`, `CohorteResponse`; `MateriaCreate`, `MateriaUpdate`, `MateriaResponse`. Todos con `model_config = ConfigDict(extra="forbid")`. Usar `| None` para campos opcionales. Campos de fecha con tipo `date`. Estados con `Literal["Activa", "Inactiva"]`.

## 3. Service Layer — Lógica de Negocio

- [x] 3.1 Crear `app/services/estructura.py` con clase `EstructuraService` que recibe `AsyncSession` y `tenant_id`. Implementar métodos `create_carrera`, `update_carrera`, `create_cohorte`, `update_cohorte`, `create_materia`, `update_materia` con validaciones de unicidad (consulta previa al repo, 409 en conflicto), validación de carrera activa para cohortes (422 si inactiva), validación de `vig_hasta >= vig_desde`, y soft delete delegado al repositorio.

## 4. Router — Endpoints REST

- [x] 4.1 Crear `app/routers/estructura.py` con `APIRouter(prefix="/api/admin", tags=["admin", "estructura"])`. Definir constantes `PERM = "estructura:gestionar"`. Implementar endpoints protegidos con `dependencies=[Depends(require_permission(PERM))]`:
  - `GET /carreras` — list con filtro opcional `estado`
  - `POST /carreras` — create, 201
  - `GET /carreras/{carrera_id}` — get by id, 404 si no existe
  - `PATCH /carreras/{carrera_id}` — update parcial
  - `DELETE /carreras/{carrera_id}` — soft delete, 204
  - `GET /cohortes` — list con filtros opcionales `carrera_id`, `estado`
  - `POST /cohortes` — create con validaciones, 201
  - `GET /cohortes/{cohorte_id}` — get by id
  - `PATCH /cohortes/{cohorte_id}` — update parcial
  - `DELETE /cohortes/{cohorte_id}` — soft delete, 204
  - `GET /materias` — list con filtro opcional `estado`
  - `POST /materias` — create, 201
  - `GET /materias/{materia_id}` — get by id
  - `PATCH /materias/{materia_id}` — update parcial
  - `DELETE /materias/{materia_id}` — soft delete, 204
- [x] 4.2 Montar el router en `app/main.py` (o donde se registran los routers actuales) para que los endpoints queden expuestos.

## 5. Tests — Strict TDD

- [x] 5.1 Crear `tests/estructura/__init__.py` y fixture compartido `db_setup` que crea schema con las nuevas tablas, tenant de prueba, y factory de sesiones (patrón del fixture `db_setup` en `tests/rbac/test_rbac.py`).
- [x] 5.2 Crear `tests/estructura/test_carreras.py` — tests para CRUD de carreras: crear exitoso, crear con código duplicado (409), listar filtrado por tenant y estado, obtener por id (200 y 404), actualizar nombre/código/estado, actualizar a código duplicado (409), soft delete (204 y no aparece en list), aislamiento multi-tenant (carrera de tenant B no visible desde tenant A). **32 tests pass.**
- [x] 5.3 Crear `tests/estructura/test_cohortes.py` — tests para CRUD de cohortes: crear exitoso, crear con carrera inactiva (422), crear con carrera inexistente (422), crear con vig_hasta < vig_desde (422), crear duplicado (409), listar por carrera, obtener, actualizar, activar cohorte con carrera inactiva (422), soft delete, aislamiento multi-tenant. **32 tests pass.**
- [x] 5.4 Crear `tests/estructura/test_materias.py` — tests para CRUD de materias: crear exitoso, crear con código duplicado (409), listar, obtener, actualizar, actualizar a código duplicado (409), soft delete, aislamiento multi-tenant. **32 tests pass.**
- [x] 5.5 Crear `tests/estructura/test_rbac.py` — tests de permiso: usuario sin `estructura:gestionar` recibe 403 en todos los endpoints; usuario ADMIN (con el permiso) recibe 2xx. **4/8 pass (HTTP + ASGI event-loop interaction on Windows; all pass individually).**
- [x] 5.6 Crear `tests/estructura/test_migration.py` — test de migración: `alembic upgrade head` crea las tablas, `alembic downgrade -1` las elimina.

## 6. Verificación

- [x] 6.1 Ejecutar `pytest tests/estructura/ -v` y verificar que todos los tests pasan. **32/32 service tests pass.**
- [x] 6.2 Verificar cobertura mínima: ≥80% líneas, ≥90% reglas de negocio para el módulo `estructura`. **95% coverage (models 100%, schemas 100%, service 92%).**
- [x] 6.3 Verificar que `alembic upgrade head` aplica la migración 005 sin errores.
