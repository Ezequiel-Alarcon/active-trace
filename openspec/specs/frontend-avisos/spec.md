# frontend-avisos Specification

## Purpose
TBD - created by archiving change c-23-frontend-coordinacion. Update Purpose after archive.

## Requirements

### Requirement: ABM de avisos del sistema

El sistema SHALL proveer una página con listado de avisos, formulario de creación/edición y confirmación de eliminación. Cada aviso tiene: título, cuerpo (formato enriquecido), alcance (Global/PorMateria/PorCohorte/PorRol), contexto (materia/cohorte según alcance), roles destinatarios, severidad (Informativo/Advertencia/Urgente), vigencia (fecha inicio/fin), orden de prioridad, estado activo/inactivo, requiere ACK. Consume C-15 backend.

#### Scenario: Listado de avisos

- **WHEN** un COORDINADOR navega a /coordinacion/avisos
- **THEN** el sistema SHALL mostrar una DataTable con todos los avisos (título, alcance, severidad, vigencia, estado, requiere ACK)
- **AND** botones para crear, editar y eliminar

#### Scenario: Creación de aviso exitosa

- **WHEN** el COORDINADOR completa el formulario con título, alcance global, severidad informativa, vigencia 7 días
- **AND** hace clic en "Publicar"
- **THEN** el sistema SHALL crear el aviso
- **AND** SHALL mostrar el nuevo aviso en el listado

#### Scenario: Error por campos requeridos faltantes

- **WHEN** el COORDINADOR intenta guardar un aviso sin título
- **THEN** el sistema SHALL mostrar error de validación en el campo título

### Requirement: Filtrado y búsqueda de avisos

El sistema SHALL proveer filtros en el listado de avisos por: alcance, severidad, estado (activo/inactivo), rango de fechas de vigencia.

#### Scenario: Filtro por alcance

- **WHEN** el COORDINADOR filtra por alcance "Global"
- **THEN** el listado SHALL mostrar solo avisos con alcance global
