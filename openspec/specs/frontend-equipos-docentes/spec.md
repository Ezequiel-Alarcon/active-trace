# frontend-equipos-docentes Specification

## Purpose
TBD - created by archiving change c-23-frontend-coordinacion. Update Purpose after archive.

## Requirements

### Requirement: Vista "Mis Equipos" para el usuario autenticado (COORDINADOR/ADMIN)

El sistema SHALL proveer una página que liste las comisiones y materias donde el usuario está asignado, mostrando rol, carrera, cohorte, comisiones, vigencia y estado. SHALL incluir filtros por estado, materia, rol, carrera y cohorte. Consume GET /api/equipos/mis-equipos (C-08).

#### Scenario: Vista inicial muestra asignaciones activas del usuario

- **WHEN** un COORDINADOR navega a /coordinacion/equipos
- **THEN** el sistema SHALL mostrar una DataTable con sus asignaciones activas (rol, materia, carrera, cohorte, vigencia, estado)
- **AND** SHALL mostrar un EmptyState si no tiene asignaciones

#### Scenario: Filtros de equipo

- **WHEN** el COORDINADOR selecciona un filtro de estado "Activo"
- **THEN** la tabla SHALL actualizarse mostrando solo asignaciones activas

### Requirement: Asignación masiva de docentes

El sistema SHALL proveer un formulario multi-paso para asignar múltiples docentes a una combinación materia × carrera × cohorte × rol con vigencia. Consume POST /api/equipos/asignacion-masiva (C-08).

#### Scenario: Asignación masiva exitosa

- **WHEN** el COORDINADOR completa el formulario con 3 docentes, una materia, carrera, cohorte, rol y vigencia
- **AND** confirma la asignación
- **THEN** el sistema SHALL mostrar un mensaje de éxito con la cantidad de asignaciones creadas
- **AND** la tabla de equipos SHALL reflejar las nuevas asignaciones

#### Scenario: Error en asignación masiva (docente ya asignado)

- **WHEN** el COORDINADOR intenta asignar un docente ya asignado al mismo contexto
- **THEN** el sistema SHALL mostrar un mensaje de error indicando los conflictos

### Requirement: Clonar equipo entre períodos

El sistema SHALL proveer un formulario para seleccionar un equipo origen (materia × carrera × cohorte) y un destino, y duplicar todas las asignaciones vigentes. Consume POST /api/equipos/clonar (C-08, RN-12).

#### Scenario: Clonado exitoso

- **WHEN** el COORDINADOR selecciona origen MateriaA/CarreraX/Cohorte2025 y destino MateriaA/CarreraX/Cohorte2026
- **AND** confirma la operación
- **THEN** el sistema SHALL mostrar las nuevas asignaciones clonadas con las fechas del nuevo período

### Requirement: Modificar vigencia general del equipo

El sistema SHALL proveer una acción que actualice las fechas de vigencia de todas las asignaciones de un equipo seleccionado. Consume PATCH /api/equipos/vigencia (C-08).

#### Scenario: Modificación de vigencia exitosa

- **WHEN** el COORDINADOR selecciona un equipo y establece nueva fecha "desde" y "hasta"
- **AND** confirma
- **THEN** el sistema SHALL actualizar las vigencias de todas las asignaciones del equipo

### Requirement: Exportar equipo docente

El sistema SHALL proveer un botón de exportación que descargue un archivo con el detalle de asignaciones del equipo. Consume GET /api/equipos/exportar (C-08).

#### Scenario: Exportación exitosa

- **WHEN** el COORDINADOR hace clic en "Exportar equipo"
- **THEN** el sistema SHALL descargar un archivo CSV/XLSX con las asignaciones
