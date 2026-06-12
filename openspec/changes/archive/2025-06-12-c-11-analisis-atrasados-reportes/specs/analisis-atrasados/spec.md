# Analisis-Atrasados Spec

## ADDED Requirements

### Requirement: Alumno atrasado — definición formal

Un alumno se considera **atrasado** en una actividad cuando:
- La actividad existe en `VersionPadron` (para la `materia_id` y `cohorte_id` del alumno), Y
- NO existe `Calificacion` para ese `(materia_id, usuario_id, asignacion_id)`, O
- Existe `Calificacion` pero `derivar_aprobado(nota, umbral_pct, conjunto_aprobado)` retorna `False`

La lógica es **derivada**, no almacenada. El sistema computa el estado en cada query.

#### Scenario: Alumno sin calificación para actividad esperada
- **WHEN** existe `EntradaPadron` para `(materia_id, cohorte_id, usuario_id)` y existe `Asignacion` en `VersionPadron`, pero NO existe `Calificacion` para `(materia_id, usuario_id, asignacion_id)`
- **THEN** el alumno está atrasado en esa actividad

#### Scenario: Alumno con calificación insuficiente
- **WHEN** existe `Calificacion` para `(materia_id, usuario_id, asignacion_id)` con `nota = 4` y `UmbralMateria.umbral_pct = 60`
- **THEN** `derivar_aprobado(4, 60, [])` retorna `False`, el alumno está atrasado

#### Scenario: Alumno aprobado
- **WHEN** existe `Calificacion` con `nota = 80` y `UmbralMateria.umbral_pct = 60`
- **THEN** `derivar_aprobado(80, 60, [])` retorna `True`, el alumno NO está atrasado

#### Scenario: Alumno con nota textual aprobada
- **WHEN** existe `Calificacion` con `nota = "A"` y `UmbralMateria.conjunto_aprobado = ["A", "B", "C"]`
- **THEN** `derivar_aprobado("A", 60, ["A","B","C"])` retorna `True`, el alumno NO está atrasado

### Requirement: Endpoint GET /api/analisis/atrasados

El sistema SHALL expose un endpoint `GET /api/analisis/atrasados` que retorna alumnos atrasados con los siguientes filtros:

- `materia_id` (UUID, opcional): filtrar por materia
- `cohorte_id` (UUID, opcional): filtrar por cohorte
- `tutor_id` (UUID, opcional): filtrar solo alumnos asignados a ese tutor
- `limit` (int, default 50, max 200): paginación
- `offset` (int, default 0): paginación

**Scope basado en rol JWT**:
- PROFESOR: solo sus materias asignadas
- TUTOR: solo sus tutorados
- COORDINADOR/ADMIN: todo el tenant

El response incluye para cada alumno:
- `usuario_id`, `email` (cifrado), `nombre`
- `materia_id`, `materia_nombre`
- `asignacion_id`, `asignacion_nombre`
- `estado`: `"sin_nota"` | `"no_aprobado"`
- `nota_actual`: valor de la calificación o `null`
- `umbral_pct`: umbral aplicado

#### Scenario: Profesor consulta sus alumnos atrasados
- **WHEN** usuario con rol PROFESOR y `materias_asignadas = [materia_A]` llama `GET /api/analisis/atrasados`
- **THEN** el resultado solo incluye alumnos atrasados de `materia_A`

#### Scenario: Sin resultados
- **WHEN** no hay alumnos atrasados para los filtros dados
- **THEN** retorna array vacío con status 200

### Requirement: Endpoint GET /api/analisis/ranking

El sistema SHALL expose un endpoint `GET /api/analisis/ranking` que retorna el ranking de alumnos por cantidad de actividades aprobadas.

Parámetros:
- `materia_id` (UUID, requerido): materia a rankinguear
- `limit` (int, default 50, max 200): cantidad de resultados

El ranking usa window function:
```sql
ROW_NUMBER() OVER (
    PARTITION BY materia_id
    ORDER BY COUNT(aprobadas) DESC, AVG(nota_numerica) DESC
) as posicion
```

El response incluye:
- `posicion` (int): ranking (1 = más aprobadas)
- `usuario_id`, `nombre`, `email`
- `cantidad_aprobadas` (int)
- `cantidad_totales` (int)
- `nota_promedio` (float | null)

#### Scenario: Ranking con empate en aprobadas
- **WHEN** dos alumnos tienen 5 aprobadas, pero uno tiene promedio 8.5 y otro 7.0
- **THEN** el de promedio 8.5 aparece primero (desempate por nota_promedio DESC)

### Requirement: Permisos para analisis

Los endpoints de analisis requieren el permiso `analisis:ver`.

#### Scenario: Usuario sin permiso accede a analisis
- **WHEN** usuario sin `analisis:ver` llama `GET /api/analisis/atrasados`
- **THEN** el sistema retorna 403 Forbidden