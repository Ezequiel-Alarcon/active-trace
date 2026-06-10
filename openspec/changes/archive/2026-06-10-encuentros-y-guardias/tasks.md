## 1. Migración 008

- [x] 1.1 Crear `alembic/versions/008_encuentros_guardias.py` con `down_revision = "007_programas_fechas"`
- [x] 1.2 Definir `upgrade()`: crear tablas `slot_encuentro`, `instancia_encuentro`, `guardia` con columnas, FKs e índices según diseño
- [x] 1.3 Definir `downgrade()`: `DROP TABLE IF EXISTS ... CASCADE` en orden inverso
- [x] 1.4 Ejecutar `alembic upgrade head` y verificar que las tablas existen

## 2. Modelos ORM

- [x] 2.1 Crear `app/models/slot_encuentro.py` — modelo `SlotEncuentro` con enum `DiaSemana` (0=Lunes..6=Domingo), FKs a `materia` y `cohorte`, campos `titulo`, `hora_inicio`, `hora_fin`, `fecha_inicio`, `cant_semanas`, `meet_url`, `video_url`. Índices: `ix_slot_encuentro_tenant_materia_cohorte`, `ix_slot_encuentro_tenant_deleted`
- [x] 2.2 Crear `app/models/instancia_encuentro.py` — modelo `InstanciaEncuentro` con enum `EstadoEncuentro` (Programado, Realizado, Cancelado), FK a `slot_encuentro` (nullable), FKs a `materia` y `cohorte`, campos `fecha`, `hora_inicio`, `hora_fin`, `titulo`, `estado`, `meet_url`, `video_url`, `comentario`. Índices: `ix_instancia_encuentro_tenant_materia_cohorte`, `ix_instancia_encuentro_tenant_slot`, `ix_instancia_encuentro_tenant_deleted`
- [x] 2.3 Crear `app/models/guardia.py` — modelo `Guardia` con FK a `usuario` (`tutor_id`), FKs a `materia` y `cohorte`, campos `fecha`, `hora_inicio`, `hora_fin`, `titulo`, `observaciones`. Índices: `ix_guardia_tenant_tutor`, `ix_guardia_tenant_materia_cohorte`, `ix_guardia_tenant_deleted`
- [x] 2.4 Registrar los nuevos modelos en `app/models/__init__.py`

## 3. Schemas Pydantic

- [x] 3.1 Crear `app/schemas/encuentros.py` con schemas para SlotEncuentro: `SlotEncuentroCreate` (validar `cant_semanas` entre 1 y 52), `SlotEncuentroUpdate`, `SlotEncuentroResponse` (incluye lista de instancias)
- [x] 3.2 Agregar schemas para InstanciaEncuentro: `InstanciaEncuentroCreate` (encuentro único), `InstanciaEncuentroUpdate` (estado, meet_url, video_url, comentario), `InstanciaEncuentroResponse`
- [x] 3.3 Todos los schemas con `model_config = ConfigDict(extra="forbid")`

## 4. Schemas de Guardia

- [x] 4.1 Crear `app/schemas/guardias.py` con: `GuardiaCreate` (sin `tutor_id` — se toma de sesión), `GuardiaUpdate`, `GuardiaResponse`
- [x] 4.2 `GuardiaResponse` debe incluir `tutor_nombre` (resuelto desde la FK) para el export y listados

## 5. Service de Encuentros

- [x] 5.1 Crear `app/services/encuentros.py` con clase `EncuentrosService(session, tenant_id)`
- [x] 5.2 Método `create_slot(data: SlotEncuentroCreate)` — crea slot + genera `cant_semanas` instancias en un loop. Validar `cant_semanas` 1..52. Usar `datetime.date` + `timedelta(weeks=i)` para calcular fechas
- [x] 5.3 Método `create_instancia_unica(data: InstanciaEncuentroCreate)` — crea instancia con `slot_id=None`
- [x] 5.4 Métodos `get_slot`, `list_slots`, `update_slot`, `delete_slot` — siguiendo patrón de `EstructuraService`
- [x] 5.5 Métodos `get_instancia`, `list_instancias(con filtros)`, `update_instancia`, `delete_instancia`
- [x] 5.6 Método `generar_fragmento_lms(materia_id, cohorte_id)` — genera HTML con tabla de instancias ordenadas por fecha. Si `meet_url` existe, incluir como link. Instancias canceladas marcadas visualmente

## 6. Service de Guardias

- [x] 6.1 Crear `app/services/guardias.py` con clase `GuardiaService(session, tenant_id, current_user_id, current_user_roles)`
- [x] 6.2 Método `create_guardia(data: GuardiaCreate)` — setea `tutor_id` desde `current_user_id`
- [x] 6.3 Método `list_guardias(filtros)` — si el usuario es TUTOR, agregar filtro `tutor_id == current_user_id`; si COORDINADOR/ADMIN, sin filtro de tutor
- [x] 6.4 Métodos `get_guardia`, `update_guardia`, `delete_guardia` — TUTOR solo accede a las propias (404 si ajena)
- [x] 6.5 Método `export_guardias_csv(filtros)` — genera CSV con `csv.DictWriter`, uniendo `usuario.nombre`, `materia.codigo`, `cohorte.nombre`

## 7. Routers

- [x] 7.1 Crear `app/routers/encuentros.py` con `APIRouter(prefix="/api/encuentros", tags=["encuentros"])`
- [x] 7.2 Endpoints de slots: `GET /slots`, `POST /slots` (guard `encuentros:gestionar`), `GET /slots/{slot_id}`, `PATCH /slots/{slot_id}`, `DELETE /slots/{slot_id}`
- [x] 7.3 Endpoints de instancias: `GET /instancias`, `POST /instancias/unico`, `GET /instancias/{instancia_id}`, `PATCH /instancias/{instancia_id}`, `DELETE /instancias/{instancia_id}`
- [x] 7.4 Endpoint `GET /instancias/fragmento-lms` — query params `materia_id`, `cohorte_id` requeridos. Retorna `HTMLResponse`
- [x] 7.5 Crear `app/routers/guardias.py` con `APIRouter(prefix="/api/guardias", tags=["guardias"])`
- [x] 7.6 Endpoints de guardias: `GET /` (TUTOR usa `encuentros:registrar_guardia`, COORD/ADMIN usan `encuentros:gestionar`), `POST /`, `GET /{guardia_id}`, `PATCH /{guardia_id}`, `DELETE /{guardia_id}`
- [x] 7.7 Endpoint `GET /export` — solo COORDINADOR/ADMIN (guard `encuentros:gestionar`). Retorna `StreamingResponse` con CSV
- [x] 7.8 Registrar ambos routers en `app/api/v1/main_router.py`
