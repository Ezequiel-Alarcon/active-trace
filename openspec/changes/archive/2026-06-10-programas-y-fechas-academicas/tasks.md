## 1. Data Layer — Migration y Modelos

- [x] 1.1 Crear migración `007_programas_fechas` con tablas `programa_materia` y `fecha_academica`, índices de unicidad compuestos por `tenant_id`, FKs a `materia`, `carrera`, `cohorte`, y columnas de soft delete. Down revision: `006_usuarios_asignaciones` si existe; si no, `005_estructura_academica` como fallback temporal (ajustar cuando C-07 migre).
- [x] 1.2 Crear modelo `ProgramaMateria` en `app/models/programa_materia.py` con `TenantScopedMixin`, FK a `materia.id`, `carrera.id`, `cohorte.id` (ON DELETE RESTRICT), campos `titulo` (String 255), `referencia_archivo` (String 512, nullable), e índices `ix_programa_materia_tenant_materia_carrera_cohorte` (unique) y `ix_programa_materia_tenant_deleted`.
- [x] 1.3 Crear modelo `FechaAcademica` en `app/models/fecha_academica.py` con `TenantScopedMixin`, enum `TipoFechaAcademica` (Parcial, TP, Coloquio), FK a `materia.id` y `cohorte.id` (ON DELETE RESTRICT), campos `tipo` (SAEnum), `numero_instancia` (Integer), `fecha` (Date), `titulo` (String 255, nullable), `descripcion` (Text, nullable), e índices `ix_fecha_academica_tenant_materia_cohorte_tipo_num` (unique) y `ix_fecha_academica_tenant_deleted`.
- [x] 1.4 Registrar ambos modelos en `app/models/__init__.py` para que `Base.metadata` los incluya y Alembic los detecte.

## 2. Schemas — Pydantic DTOs

- [x] 2.1 Crear `app/schemas/programas_fechas.py` con schemas para `ProgramaMateria`: `ProgramaCreate`, `ProgramaUpdate`, `ProgramaResponse`. `ProgramaUpdate` solo permite cambiar `titulo` y `referencia_archivo` (materia_id, carrera_id, cohorte_id son inmutables). Todos con `model_config = ConfigDict(extra="forbid")`.
- [x] 2.2 Agregar schemas para `FechaAcademica` en el mismo archivo: `FechaAcademicaCreate`, `FechaAcademicaUpdate`, `FechaAcademicaResponse`. `FechaAcademicaUpdate` solo permite cambiar `fecha`, `titulo`, `descripcion` (tipo y numero_instancia son inmutables). `tipo` usa `Literal["Parcial", "TP", "Coloquio"]`. Todos con `extra='forbid'`.
- [x] 2.3 Agregar schema `FragmentoLmsResponse` con `content_type: str` y `html: str` para el endpoint de fragmento LMS.

## 3. Service Layer — Lógica de Negocio

- [x] 3.1 Crear `app/services/programas_fechas.py` con clase `ProgramaFechasService` que recibe `AsyncSession` y `tenant_id`.
- [x] 3.2 Implementar métodos de ProgramaMateria: `create_programa`, `update_programa`, `get_programa`, `list_programas`, `delete_programa`. Validación de unicidad `(materia_id, carrera_id, cohorte_id)` con 409 en conflicto. No se permite cambiar materia_id, carrera_id ni cohorte_id en update.
- [x] 3.3 Implementar métodos de FechaAcademica: `create_fecha`, `update_fecha`, `get_fecha`, `list_fechas`, `delete_fecha`. Validación de unicidad `(materia_id, cohorte_id, tipo, numero_instancia)` con 409 en conflicto. No se permite cambiar tipo ni numero_instancia en update.
- [x] 3.4 Implementar `generar_fragmento_lms(materia_id, cohorte_id)` que consulta fechas para la materia y cohorte, las agrupa por tipo, las ordena por `numero_instancia`, y genera un string HTML con el contenido formateado (tabla o lista con fecha, titulo, descripcion). Sin fechas → mensaje "No hay fechas registradas". Soft-deleteadas excluidas.

## 4. Router — Endpoints REST

- [x] 4.1 Crear `app/routers/programas_fechas.py` con `APIRouter(prefix="/api", tags=["programas", "fechas"])`. Constante `PERM = "estructura:gestionar"`.
- [x] 4.2 Implementar endpoints de programas protegidos con `dependencies=[Depends(require_permission(PERM))]`:
  - `GET /programas` — list con filtros opcionales `materia_id`, `carrera_id`, `cohorte_id`
  - `POST /programas` — create, 201
  - `GET /programas/{programa_id}` — get by id, 404 si no existe
  - `PATCH /programas/{programa_id}` — update parcial (solo titulo y referencia_archivo)
  - `DELETE /programas/{programa_id}` — soft delete, 204
- [x] 4.3 Implementar endpoints de fechas protegidos con `dependencies=[Depends(require_permission(PERM))]`:
  - `GET /fechas-academicas` — list con filtros opcionales `materia_id`, `cohorte_id`, `tipo`
  - `POST /fechas-academicas` — create, 201
  - `GET /fechas-academicas/{fecha_id}` — get by id, 404 si no existe
  - `PATCH /fechas-academicas/{fecha_id}` — update parcial (solo fecha, titulo, descripcion)
  - `DELETE /fechas-academicas/{fecha_id}` — soft delete, 204
  - `GET /fechas-academicas/fragmento-lms` — genera HTML, query params requeridos `materia_id` y `cohorte_id`
- [x] 4.4 Montar el router en `app/main.py` (o donde se registran los routers actuales) para que los endpoints queden expuestos.

## 5. Tests — Strict TDD

- [x] 5.1 Crear `tests/programas_fechas/__init__.py` y fixture compartido que crea schema con las nuevas tablas, tenant de prueba, y datos de estructura (carrera, cohorte, materia) necesarios para los tests.
- [x] 5.2 Crear `tests/programas_fechas/test_programas.py` — tests para CRUD de programas: crear exitoso, crear sin referencia_archivo, crear con duplicado materia×carrera×cohorte (409), crear con extra fields (422), listar filtrado por materia/carrera/cohorte, obtener por id (200 y 404), actualizar titulo y referencia_archivo, intentar cambiar materia_id (rechazado), soft delete (204 y no aparece en list), aislamiento multi-tenant.
- [x] 5.3 Crear `tests/programas_fechas/test_fechas.py` — tests para CRUD de fechas: crear exitoso, crear con campos minimos, crear con tipo invalido (422), crear duplicado tipo×numero para misma materia×cohorte (409), listar ordenado por fecha, listar filtrado por materia/cohorte/tipo, obtener por id (200 y 404), actualizar fecha/titulo/descripcion, intentar cambiar tipo (422), intentar cambiar numero_instancia (422), soft delete (204), aislamiento multi-tenant.
- [x] 5.4 Crear `tests/programas_fechas/test_fragmento_lms.py` — tests para fragmento LMS: generar con fechas (HTML contiene todas), generar sin fechas (mensaje "no hay fechas"), soft-deleteadas excluidas, agrupacion por tipo, ordenamiento por numero_instancia, sin materia_id/cohorte_id (422), aislamiento multi-tenant.
- [x] 5.5 Crear `tests/programas_fechas/test_rbac.py` — tests de permiso: usuario sin `estructura:gestionar` recibe 403 en todos los endpoints de programas, fechas y fragmento-lms; usuario ADMIN (con el permiso) recibe 2xx.
- [x] 5.6 Crear `tests/programas_fechas/test_migration.py` — test de migración: `alembic upgrade head` crea las tablas, `alembic downgrade -1` las elimina.

## 6. Verificación

- [x] 6.1 Ejecutar `pytest tests/programas_fechas/ -v` y verificar que todos los tests pasan.
- [x] 6.2 Verificar cobertura minima: >=80% lineas, >=90% reglas de negocio para el modulo `programas_fechas`.
- [x] 6.3 Verificar que `alembic upgrade head` aplica la migracion 007 sin errores.
