## 1. Schemas (app/schemas/equipos.py)

- [x] 1.1 Crear archivo `app/schemas/equipos.py` con `extra='forbid'` en todos los schemas
- [x] 1.2 `EquipoAsignacionResponse` — extiende `AsignacionResponse` con `nombre_usuario`, `apellidos_usuario`, `email_usuario`, `nombre_rol`, `nombre_contexto` (materia/carrera/cohorte)
- [x] 1.3 `AsignacionMasivaRequest` — `usuarios_ids: list[UUID]`, `rol_id: UUID`, `contexto_tipo: str`, `contexto_id: UUID | None`, `desde: date`, `hasta: date | None`, `responsable_id: UUID | None`
- [x] 1.4 `AsignacionMasivaResponse` — `creadas: list[EquipoAsignacionResponse]`, `fallidas: list[AsignacionFallida]`
- [x] 1.5 `AsignacionFallida` — `usuario_id: UUID | None`, `motivo: str`
- [x] 1.6 `ClonarEquipoRequest` — `cohorte_origen_id: UUID`, `cohorte_destino_id: UUID`, `desde: date`, `hasta: date | None`
- [x] 1.7 `ClonarEquipoResponse` — `creadas: int`, `omitidas: int`, `fallidas: list[ClonadoFallido]`
- [x] 1.8 `ClonadoFallido` — `asignacion_origen_id: UUID`, `motivo: str`
- [x] 1.9 `VigenciaEquipoRequest` — `materia_id: UUID`, `cohorte_id: UUID`, `rol_id: UUID | None`, `desde: date`, `hasta: date | None`
- [x] 1.10 `VigenciaEquipoResponse` — `actualizadas: int`

## 2. Auditoría (app/core/audit.py)

- [x] 2.1 Agregar `ASIGNACION_MODIFICAR` al vocabulario `ACTION_CODES` en `app/core/audit.py`

## 3. Service (app/services/equipos.py)

- [x] 3.1 Crear `app/services/equipos.py` con clase `EquipoService` que recibe `AsyncSession` y `tenant_id`
- [x] 3.2 `mis_equipos(usuario_id, cohorte_id, materia_id, estado_vigencia)` — consulta asignaciones del usuario con joins a Usuario, Rol y entidades de contexto; devuelve `list[EquipoAsignacionResponse]`
- [x] 3.3 `asignacion_masiva(data: AsignacionMasivaRequest)` — itera `usuarios_ids`, valida cada uno, crea asignación individual; acumula creadas y fallidas; emite `ASIGNACION_MODIFICAR` por cada creada; devuelve `AsignacionMasivaResponse`
- [x] 3.4 `clonar_equipo(data: ClonarEquipoRequest)` — obtiene asignaciones vigentes de cohorte origen; para cada una crea copia en destino ajustando contexto; omite duplicados; rollback manual (soft-delete) ante error; emite `ASIGNACION_MODIFICAR`; devuelve `ClonarEquipoResponse`
- [x] 3.5 `modificar_vigencia(data: VigenciaEquipoRequest)` — valida materia, cohorte y rol; obtiene asignaciones vigentes filtradas; actualiza `desde`/`hasta` en bloque; emite `ASIGNACION_MODIFICAR`; devuelve `VigenciaEquipoResponse`
- [x] 3.6 `exportar_equipo(materia_id, cohorte_id, rol_id)` — obtiene asignaciones con joins a Usuario, Rol, Materia, Carrera, Cohorte; descifra emails; genera lista de dicts para CSV

## 4. Router (app/routers/equipos.py)

- [x] 4.1 Crear `app/routers/equipos.py` con `equipo_router = APIRouter(prefix="/api/equipos", tags=["equipos"])`
- [x] 4.2 Dependencia `_get_equipo_service` que inyecta `EquipoService` con `tenant_id` del JWT
- [x] 4.3 `GET /api/equipos/mis-equipos` — guard `require_permission("equipos:asignar")`; usa `current_user.user_id` del JWT como `usuario_id`; query params `cohorte_id`, `materia_id`, `estado_vigencia`
- [x] 4.4 `POST /api/equipos/asignacion-masiva` — guard `require_permission("equipos:asignar")`; body `AsignacionMasivaRequest`; response `AsignacionMasivaResponse`
- [x] 4.5 `POST /api/equipos/clonar` — guard `require_permission("equipos:asignar")`; body `ClonarEquipoRequest`; response `ClonarEquipoResponse`
- [x] 4.6 `PATCH /api/equipos/vigencia` — guard `require_permission("equipos:asignar")`; body `VigenciaEquipoRequest`; response `VigenciaEquipoResponse`
- [x] 4.7 `GET /api/equipos/exportar` — guard `require_permission("equipos:asignar")`; query params `materia_id`, `cohorte_id`, `rol_id`; devuelve `StreamingResponse` con CSV (BOM UTF-8, `text/csv`, `Content-Disposition: attachment`)

## 5. Montaje del router (app/api/v1/main_router.py)

- [x] 5.1 Importar e incluir `equipo_router` en `main_router` en `app/api/v1/main_router.py`

## 6. Tests (tests/test_equipos.py)

- [x] 6.1 Crear `tests/test_equipos.py` con fixtures: tenant de test, usuarios de prueba (PROFESOR, COORDINADOR), cohortes, materias, asignaciones preexistentes
- [x] 6.2 Test `mis_equipos`: docente ve solo sus asignaciones, filtra por cohorte, filtra por vigencia, sin asignaciones devuelve vacío
- [x] 6.3 Test `asignacion_masiva`: lote exitoso, lote con fallos parciales (usuario inexistente), rol inexistente, contexto inexistente, fechas inválidas, sin permisos
- [x] 6.4 Test `clonar_equipo`: clonado exitoso entre cohortes, omite duplicados, cohorte origen inexistente, cohorte destino inexistente, rollback ante error, cohorte origen sin asignaciones
- [x] 6.5 Test `modificar_vigencia`: actualiza vigentes, no afecta vencidas, filtra por rol, sin asignaciones que coincidan, fechas inválidas, materia inexistente
- [x] 6.6 Test `exportar_equipo`: CSV con datos esperados, filtro por rol, sin asignaciones devuelve headers solamente, BOM presente, sin permisos
- [x] 6.7 Test de auditoría: verificar que `ASIGNACION_MODIFICAR` se emite en operaciones batch (masiva, clonar, vigencia)
