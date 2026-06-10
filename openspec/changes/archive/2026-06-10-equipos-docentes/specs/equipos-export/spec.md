## ADDED Requirements

### Requirement: Exportar equipo docente a CSV
El sistema SHALL permitir a un COORDINADOR o ADMIN descargar un archivo CSV con la composición del equipo docente, incluyendo datos del usuario (nombre, apellidos, email descifrado), rol, materia, carrera, cohorte y fechas de vigencia, filtrable por `materia_id`, `cohorte_id` y `rol_id`.

#### Scenario: Exportación exitosa de equipo
- **WHEN** un COORDINADOR solicita `GET /api/equipos/exportar?materia_id=<uuid>&cohorte_id=<uuid>`
- **THEN** el sistema devuelve un `StreamingResponse` con `Content-Type: text/csv; charset=utf-8` y `Content-Disposition: attachment; filename="equipo_<materia>_<cohorte>.csv"`, conteniendo las columnas: nombre, apellidos, email, rol, materia, carrera, cohorte, desde, hasta, estado_vigencia

#### Scenario: Exportación con filtro de rol
- **WHEN** un COORDINADOR solicita `GET /api/equipos/exportar?materia_id=<uuid>&cohorte_id=<uuid>&rol_id=<uuid>`
- **THEN** el CSV solo incluye asignaciones del rol especificado

#### Scenario: Exportación con BOM para Excel
- **WHEN** un COORDINADOR solicita `GET /api/equipos/exportar?materia_id=<uuid>&cohorte_id=<uuid>`
- **THEN** el archivo CSV comienza con el byte order mark UTF-8 (`\ufeff`) para compatibilidad con Microsoft Excel

#### Scenario: Exportación sin asignaciones que coincidan
- **WHEN** un COORDINADOR solicita `GET /api/equipos/exportar` con filtros que no matchean ninguna asignación
- **THEN** el sistema devuelve un CSV que contiene solo la fila de encabezados (headers), con status 200

#### Scenario: Exportación sin permisos
- **WHEN** un PROFESOR autenticado solicita `GET /api/equipos/exportar`
- **THEN** el sistema devuelve 403 Forbidden

#### Scenario: Exportación sin filtros obligatorios
- **WHEN** un COORDINADOR solicita `GET /api/equipos/exportar` sin `materia_id`
- **THEN** el sistema devuelve 422 con detalle indicando que `materia_id` es requerido

### Requirement: Columnas del CSV de exportación
El sistema SHALL incluir las siguientes columnas en el CSV de exportación, en orden: `nombre`, `apellidos`, `email`, `rol`, `materia`, `carrera`, `cohorte`, `desde`, `hasta`, `estado_vigencia`. El email SHALL ser el valor descifrado (no el hash ni el ciphertext).

#### Scenario: CSV con datos descifrados
- **WHEN** se exporta un equipo que incluye al usuario con email "profesor@institucion.edu"
- **THEN** la columna `email` del CSV contiene "profesor@institucion.edu" (descifrado)

#### Scenario: CSV con hasta nulo
- **WHEN** una asignación tiene `hasta == None` (vigencia indefinida)
- **THEN** la columna `hasta` del CSV contiene cadena vacía
