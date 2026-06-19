## Why

Al levantar el proyecto end-to-end se descubrió que C-10 (calificaciones-import) y C-11 (análisis) se archivaron como "hechos" pero quedaron **stubbeados**: los endpoints de análisis devuelven vacío hardcodeado (ignoran la DB), falta el endpoint `/api/comisiones` que el frontend consume para el selector del workspace, y `import/confirm` tiene un bug que impide persistir. El frontend (C-21/C-22) se testeó contra mocks (MSW), así que se ve completo y pasa sus tests, pero contra el backend real las tablas (Atrasados, Ranking, Notas finales, Reportes) muestran siempre el estado vacío. Estos defectos están marcados con `# TODO:` en el código (regla #18). Este change los corrige con TDD real contra la base (sin mocks de DB), de modo que el flujo central del PROFESOR (importar → analizar) funcione de punta a punta.

## What Changes

- **FIX** `POST /api/calificaciones/import/confirm`: hoy usa `Depends()` dentro del cuerpo de la función (no resuelve la dependencia) → el import nunca persiste. Se inyecta la dependencia como parámetro del endpoint (igual que `import_preview`).
- **NEW** `GET /api/comisiones`: lista las comisiones (materia × cohorte) disponibles para el usuario autenticado, con la forma que espera el frontend (`id, materia_id, materia_nombre, cohorte_id, cohorte_nombre`). Sin esto, el workspace no permite seleccionar comisión ni arrancar la importación.
- **FIX** `GET /api/analisis/atrasados`: dejar de devolver `alumnos=[]` hardcodeado; implementar la query real (alumnos con actividad faltante o nota bajo umbral), con email descifrado y nombre de materia. Implementar `AnalisisRepository.get_alumnos_atrasados` (hoy retorna `[]`).
- **FIX** `GET /api/analisis/ranking`: wire del router al service/repo; corregir la semántica de "aprobadas" (contar sólo las que aprueban según el umbral, vía `derivar_aprobado`), ordenado desc.
- **FIX** `GET /api/reportes/notas-finales` y `GET /api/reportes/materia/{id}`: devolver los datos reales que ya calcula el service (hoy se descartan: `notas=[]`, `alumnos=[]`), con nombres de materia.
- **Tests TDD contra DB real** (base efímera, sin mocks): seed → llamada al endpoint → asserts de filas, cubriendo cada endpoint y el caso vacío. Esta vez se prueba el **router devolviendo datos**, no sólo el service aislado (la causa raíz del defecto original).

## Capabilities

### New Capabilities
- `comisiones-listado`: endpoint `GET /api/comisiones` que devuelve las comisiones (materia × cohorte) visibles para el usuario, en la forma consumida por el frontend.
- `analisis-academico`: implementación real de los endpoints de análisis del PROFESOR — atrasados, ranking, notas finales y reporte por materia — leyendo la DB, con email PII descifrado y nombres de materia. Reemplaza los stubs vacíos.

### Modified Capabilities
- `calificaciones-import`: corrige `import/confirm` para que persista las filas válidas del preview (hoy rompe por mal uso de `Depends()`). *(Si no existe spec previa en `openspec/specs/`, se introduce como capability nueva `calificaciones-import-confirm`.)*

## Impact

- **Código modificado**: `backend/app/api/v1/analisis.py` (4 routers), `backend/app/api/v1/calificaciones.py` (import/confirm), `backend/app/domain/analisis/repositories/analisis_repository.py` (queries reales), `backend/app/domain/analisis/services/analisis_service.py` (métodos atrasados/ranking enriquecidos).
- **Código nuevo**: router/endpoint `comisiones` + su service/repo; tests TDD por endpoint.
- **PII**: las respuestas exponen `email` de alumnos → se descifra con el helper AES-256 (`app.core.security.crypto.decrypt`) sólo en la capa de respuesta, nunca en logs. Requiere `analisis:ver` / `reportes:ver` (fail-closed, ya presente).
- **Multi-tenancy**: todas las queries scoped por `tenant_id` (ya en el repo).
- **Sin cambios de schema/migración** previstos (los modelos `Calificacion`, `UmbralMateria`, `Materia`, `Cohorte` ya existen). Si `comisiones` necesitara una vista derivada, se resuelve por query, no por tabla nueva.
- **Frontend**: sin cambios — las respuestas respetan los tipos que ya consume (`Comision`, `AlumnoAtrasado`, `RankingEntry`, etc.).
- **Governance**: MEDIO (lógica de dominio + integración). Toca PII (descifrado de email) → revisar en code review que no se loguee. Pregunta abierta **PA-01** (Materia vs InstanciaDictado): este change adopta "comisión = materia × cohorte" como mapping pragmático; se documenta en design.md.
