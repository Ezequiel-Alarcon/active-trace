## Why

Los docentes y coordinadores necesitan subir el programa oficial de cada materia (específico por carrera y cohorte) y registrar fechas de parciales, TP y coloquios. Estos datos son la base para que los alumnos sepan qué se evalúa y cuándo, y para generar fragmentos de contenido que se publican en el aula virtual del LMS. Sin esto, el sistema no tiene información estructurada sobre la vida académica de cada materia dentro de una cohorte.

## What Changes

- Nuevo modelo ORM `ProgramaMateria`: documento por materia × carrera × cohorte, con campo `referencia_archivo` opaco (ruta/URL al archivo almacenado).
- Nuevo modelo ORM `FechaAcademica`: fechas de parciales, TP y coloquios por materia × cohorte × número de instancia.
- Migración Alembic `007_programas_fechas` que crea ambas tablas con índices de unicidad por tenant y FKs a las entidades de estructura académica.
- Schemas Pydantic v2 con `extra='forbid'` para request/response de cada entidad.
- Servicio `ProgramaFechasService` con lógica de ABM, validaciones de unicidad, y generación de fragmento LMS.
- Router `/api/programas` y `/api/fechas-academicas` protegido con `require_permission("estructura:gestionar")`.
- Endpoint `GET /api/fechas-academicas/fragmento-lms` que devuelve HTML formateado listo para copiar al aula virtual.
- Tests: CRUD de programas, CRUD de fechas, unicidad materia×carrera×cohorte, referencia de archivo opaca, fragmento LMS, aislamiento multi-tenant.

## Capabilities

### New Capabilities

- `programa-materia-crud`: ABM de programas de materia (alta, edición, consulta, soft delete). Unicidad `(tenant_id, materia_id, carrera_id, cohorte_id)`. `referencia_archivo` es una string opaca (ruta/URL); el sistema no interpreta el contenido. Filtros por materia, carrera y cohorte.
- `fecha-academica-crud`: ABM de fechas académicas (alta, edición, consulta, soft delete). Unicidad `(tenant_id, materia_id, cohorte_id, tipo, numero_instancia)`. Filtros por materia, cohorte, tipo. Ordenamiento por fecha.
- `fragmento-lms`: Generación de fragmento HTML con las fechas académicas formateadas, agrupadas por materia y tipo, listo para copiar/pegar en el aula virtual del LMS (F5.4). No es una integración automática — es contenido para uso manual.

### Modified Capabilities

_Ninguna. Este change introduce capacidades nuevas sin alterar specs existentes._

## Impact

- **Modelos**: dos nuevos archivos en `app/models/` (`programa_materia.py`, `fecha_academica.py`) + registro en `app/models/__init__.py`.
- **Migración**: `alembic/versions/007_programas_fechas.py` (down revision: `006_usuarios_asignaciones` de C-07 o, si no existe aún, placeholder en la migración).
- **Schemas**: nuevo archivo `app/schemas/programas_fechas.py` con Pydantic DTOs para request/response.
- **Servicios**: nuevo archivo `app/services/programas_fechas.py` con clase `ProgramaFechasService`.
- **Router**: nuevo archivo `app/routers/programas_fechas.py` con `APIRouter(prefix="/api", tags=["programas", "fechas"])` montado en `/api/programas` y `/api/fechas-academicas`.
- **Tests**: `tests/programas_fechas/test_programas.py`, `test_fechas.py`, `test_fragmento_lms.py`, `test_rbac.py`.
- **RBAC**: el permiso `estructura:gestionar` ya existe; ADMIN y COORDINADOR lo poseen. Sin cambios en seeds de RBAC.
- **Dependencia**: C-06 (estructura-academica) debe estar completado — los modelos Carrera, Cohorte y Materia ya existen.
