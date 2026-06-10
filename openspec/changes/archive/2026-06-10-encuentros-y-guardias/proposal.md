## Why

Los docentes necesitan gestionar encuentros sincrónicos (clases por videollamada o presenciales) y los tutores necesitan registrar guardias (horarios de consulta). Actualmente no existe un módulo que permita crear slots recurrentes con generación automática de instancias, editar el estado de cada encuentro, exportar un bloque HTML para el aula virtual ni registrar/consultar guardias. Este change cierra ese gap, habilitando las funcionalidades F6.1 a F6.6 de la épica 6.

## What Changes

- Nuevas tablas `slot_encuentro`, `instancia_encuentro`, `guardia` (migración 008).
- Endpoints `/api/encuentros/*` para gestionar slots e instancias (PROFESOR, COORDINADOR, ADMIN, NEXO vía `encuentros:gestionar`).
- Endpoints `/api/guardias/*` para registro de guardias (TUTOR con scope propio vía `encuentros:registrar_guardia`; COORDINADOR y ADMIN con vista global).
- Al crear un SlotEncuentro recurrente, el sistema genera automáticamente `cant_semanas` instancias de InstanciaEncuentro (RN-13).
- Edición de instancia individual: estado (Programado/Realizado/Cancelado), meet_url, video_url, comentario.
- Generación de fragmento HTML para incrustar en el aula virtual (F6.4).
- Export de guardias a CSV (F6.6).

## Capabilities

### New Capabilities

- `encuentros-slots`: Creación y gestión de slots de encuentro (recurrentes). Generación automática de instancias a partir del slot.
- `encuentros-instancias`: Gestión de instancias de encuentro (únicas y recurrentes). Listado con filtros (materia, cohorte, estado, rango de fechas). Edición de estado y URLs. Generación de fragmento HTML para aula virtual.
- `guardias-crud`: Registro de guardias por parte del tutor. Consulta global por coordinación. Export a CSV.

### Modified Capabilities

Ninguna. Los permisos `encuentros:gestionar` y `encuentros:registrar_guardia` ya existen en el seed de la migración 004, asignados a TUTOR, PROFESOR, COORDINADOR, ADMIN y NEXO según corresponda.

## Impact

- **Models**: Nuevos archivos `slot_encuentro.py`, `instancia_encuentro.py`, `guardia.py` en `app/models/`. Registro en `app/models/__init__.py`.
- **Schemas**: Nuevas clases Pydantic en `app/schemas/encuentros.py` y `app/schemas/guardias.py`.
- **Services**: Nuevo `EncuentrosService` en `app/services/encuentros.py`, `GuardiaService` en `app/services/guardias.py`.
- **Routers**: Nuevos routers en `app/routers/encuentros.py` y `app/routers/guardias.py`. Registro en `app/api/v1/main_router.py`.
- **Migrations**: Nueva migración 008 (`008_encuentros_guardias.py`) con `down_revision = "007_programas_fechas"`.
- **Tests**: Nuevos tests en `tests/unit/test_encuentros.py` y `tests/unit/test_guardias.py`.
- **Dependencias**: C-07 (usuarios-y-asignaciones) ya implementado — los modelos Usuario, Materia, Cohorte están disponibles. Sin dependencias nuevas.
