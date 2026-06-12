# Exportacion-TPs Spec

## ADDED Requirements

### Requirement: Endpoint GET /api/exportacion/tps-sin-corregir

El sistema SHALL expose un endpoint `GET /api/exportacion/tps-sin-corregir` que retorna una lista de actividades (TPs) sin calificar para re-importación.

Parámetros:
- `materia_id` (UUID, opcional): filtrar por materia
- `cohorte_id` (UUID, opcional): filtrar por cohorte
- `limit` (int, default 100, max 500)
- `offset` (int, default 0)

**Lógica**: actividad existe en `VersionPadron` + `EntradaPadron` pero `Calificacion.nota IS NULL` para `(materia_id, usuario_id, asignacion_id)`.

El response incluye:
- `usuario_id`, `nombre`, `email` (cifrado)
- `materia_id`, `materia_nombre`
- `cohorte_id`, `cohorte_nombre`
- `asignacion_id`, `asignacion_nombre`
- `fecha_ultima_entrega` (DateTime | null): de `Calificacion` si existe pero `nota=null`

#### Scenario: Exportar TPs sin corregir
- **WHEN** llamado `GET /api/exportacion/tps-sin-corregir`
- **THEN** retorna lista de alumnos con actividades en VersionPadron que no tienen nota

#### Scenario: Sin TPs sin corregir
- **WHEN** todas las actividades tienen calificación
- **THEN** retorna array vacío con status 200

### Requirement: Permisos para exportacion

El endpoint `/api/exportacion/tps-sin-corregir` requiere el permiso `reportes:exportar`.

#### Scenario: Usuario sin permiso intenta exportar
- **WHEN** usuario sin `reportes:exportar` llama `GET /api/exportacion/tps-sin-corregir`
- **THEN** retorna 403 Forbidden

### Requirement: Formato de exportación

El response del endpoint de exportación SHALL ser compatible con el formato de importación de C-10 (preview token flow), de modo que la lista pueda ser re-importada tras corrección.

#### Scenario: Formato compatible con import
- **WHEN** se exportan TPs sin corregir
- **THEN** el formato de cada fila incluye `usuario_id`, `materia_id`, `asignacion_id` que coinciden con los campos del import de C-10