# frontend-design-system — Delta Spec

## MODIFIED Requirements

### Requirement: Paleta de tokens visuales y colores semánticos de estado

#### ADDED Scenario: Nuevos estados semánticos para tareas y coloquios

- **WHEN** se usa <StatusBadge estado="en-progreso" /> para una tarea
- **THEN** el sistema SHALL mostrar el badge con color azul (mismo que en-envio)
- **WHEN** se usa <StatusBadge estado="resuelta" /> para una tarea
- **THEN** el sistema SHALL mostrar el badge con color verde (mismo que aprobado)
- **WHEN** se usa <StatusBadge estado="convocado" /> para un coloquio
- **THEN** el sistema SHALL mostrar el badge con color gris (mismo que neutro)
