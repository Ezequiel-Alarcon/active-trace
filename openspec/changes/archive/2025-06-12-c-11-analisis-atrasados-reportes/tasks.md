# C-11: Analisis de Atrasados y Reportes — Tasks

## 1. Permisos RBAC

- [x] 1.1 Registrar permiso `analisis:ver` en `rbac-permission-catalogue/spec.md` (delta)
- [x] 1.2 Registrar permiso `reportes:ver` en `rbac-permission-catalogue/spec.md` (delta)
- [x] 1.3 Registrar permiso `reportes:exportar` en `rbac-permission-catalogue/spec.md` (delta)
- [x] 1.4 Asignar permisos a roles: PROFESOR y TUTOR → `analisis:ver`; COORDINADOR, ADMIN → `reportes:ver`, `reportes:exportar`

## 2. Repository — AnalisisRepository

- [ ] 2.1 Crear `app/repositories/analisis_repository.py` con método `get_alumnos_atrasados(tenant_id, scope, filtros)` — query derivada con JOINs a VersionPadron, Calificacion, UmbralMateria
- [ ] 2.2 Crear método `get_ranking_aprobadas(tenant_id, materia_id, limit)` — window function ROW_NUMBER
- [ ] 2.3 Crear método `get_tps_sin_corregir(tenant_id, filtros)` — VersionPadron + Calificacion.nota IS NULL

## 3. Service — AnalisisService y ReportesService

- [ ] 3.1 Crear `app/services/analisis_service.py` con `AnalisisService`
- [ ] 3.2 Implementar `_determinar_scope(jwt_payload)` — deduce scope según rol (profesor → materias, tutor → tutorados, coord/admin → tenant)
- [ ] 3.3 Crear `app/services/reportes_service.py` con `ReportesService`
- [ ] 3.4 Implementar `reporte_materia(materia_id, tenant_id)` — agrega estado por actividad
- [ ] 3.5 Implementar `notas_finales(tenant_id, cohorte_id, filtros)` — agrupar por materia

## 4. Routers — API Endpoints

- [ ] 4.1 Crear `app/routers/analisis.py` con `require_permission("analisis:ver")`
  - `GET /api/analisis/atrasados`
  - `GET /api/analisis/ranking?materia_id=&limit=`
- [ ] 4.2 Crear `app/routers/reportes.py` con `require_permission("reportes:ver")`
  - `GET /api/reportes/materia/{materia_id}`
  - `GET /api/reportes/notas-finales?cohorte_id=&limit=&offset=`
- [ ] 4.3 Crear `app/routers/monitores.py` con permisos según endpoint
  - `GET /api/monitores/general` (analisis:ver, PROFESOR)
  - `GET /api/monitores/seguimiento` (analisis:ver, TUTOR)
  - `GET /api/monitores/coordinacion` (reportes:ver, COORDINADOR/ADMIN, params desde/hasta)
- [ ] 4.4 Crear `app/routers/exportacion.py` con `require_permission("reportes:exportar")`
  - `GET /api/exportacion/tps-sin-corregir`

## 5. Pydantic Schemas

- [x] 5.1 Crear `app/schemas/analisis.py`:
  - `AlumnoAtrasado`, `AtrasadosResponse`, `RankingEntry`, `RankingResponse`
- [x] 5.2 Crear `app/schemas/reportes.py`:
  - `ActividadEstado`, `AlumnoReporte`, `ReporteMateriaResponse`, `NotasFinalesEntry`, `NotasFinalesResponse`
- [x] 5.3 Crear `app/schemas/monitores.py`:
  - `MateriaResumen`, `MonitorGeneralResponse`, `MonitorSeguimientoResponse`, `MonitorCoordinacionResponse`
- [x] 5.4 Crear `app/schemas/exportacion.py`:
  - `TPSinCorregirEntry`, `TPSinCorregirResponse`
- [x] 5.5 Todos los schemas con `model_config = ConfigDict(extra='forbid')`

## 6. Tests de Integración

- [ ] 6.1 Test `test_alumno_sin_nota_es_atrasado` — fixture con EntradaPadron sin Calificacion
- [ ] 6.2 Test `test_alumno_con_nota_insuficiente_es_atrasado` — Calificacion.nota < umbral
- [ ] 6.3 Test `test_alumno_aprobado_no_es_atrasado` — derivar_aprobado=True
- [ ] 6.4 Test `test_ranking_ordenado_por_aprobadas` — window function
- [ ] 6.5 Test `test_ranking_desempate_por_promedio` — mismas aprobadas, diferente promedio
- [ ] 6.6 Test `test_monitor_general_scope_profesor` — solo sus materias
- [ ] 6.7 Test `test_monitor_seguimiento_scope_tutor` — solo sus tutorados
- [ ] 6.8 Test `test_monitor_coordinacion_filtro_fechas` — rango válido y rango > 365 días → 400
- [ ] 6.9 Test `test_tps_sin_corregir` — Calificacion con nota=null
- [ ] 6.10 Test permisos 403 sin rol correspondiente

## 7. Registro de Routers

- [ ] 7.1 Importar y registrar `analisis.router` en `app/main.py`
- [ ] 7.2 Importar y registrar `reportes.router` en `app/main.py`
- [ ] 7.3 Importar y registrar `monitores.router` en `app/main.py`
- [ ] 7.4 Importar y registrar `exportacion.router` en `app/main.py`