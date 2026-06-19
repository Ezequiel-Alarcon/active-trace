# frontend-setup-cuatrimestre Specification

## ADDED Requirements

### Requirement: Wizard de setup de cuatrimestre multi-paso (FL-03)

El sistema SHALL proveer un flujo guiado multi-paso para el setup de inicio de cuatrimestre. Pasos secuenciales: (1) Crear cohorte, (2) Clonar equipo docente de período anterior, (3) Ajustar asignaciones faltantes (asignación masiva), (4) Ajustar vigencias, (5) Cargar programas de materia, (6) Cargar fechas de evaluaciones, (7) Publicar aviso de bienvenida. Consume APIs de C-06, C-08, C-15, C-17.

#### Scenario: Wizard completo exitoso

- **WHEN** un COORDINADOR inicia el wizard de setup
- **AND** completa los 7 pasos en orden
- **AND** hace clic en "Finalizar" en el paso 7
- **THEN** el sistema SHALL ejecutar todas las operaciones encadenadas
- **AND** SHALL mostrar un resumen de lo creado/modificado

#### Scenario: Navegación entre pasos

- **WHEN** el COORDINADOR completa un paso
- **AND** hace clic en "Siguiente"
- **THEN** el sistema SHALL validar el paso actual
- **AND** SHALL avanzar al siguiente paso

#### Scenario: Cancelación del wizard

- **WHEN** el COORDINADOR hace clic en "Cancelar" en cualquier paso
- **THEN** el sistema SHALL confirmar la cancelación
- **AND** SHALL descartar los cambios no confirmados del paso actual

### Requirement: Barra de progreso del wizard

El sistema SHALL mostrar una barra de progreso con los 7 pasos numerados, resaltando el paso activo y marcando como completados los pasos finalizados.

#### Scenario: Barra de progreso refleja el estado

- **WHEN** el COORDINADOR está en el paso 3
- **THEN** la barra SHALL mostrar pasos 1-2 como completados, paso 3 como activo, pasos 4-7 como pendientes
