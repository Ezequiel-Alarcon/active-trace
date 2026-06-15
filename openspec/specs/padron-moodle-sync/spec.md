# padron-moodle-sync Specification

## Purpose
TBD - created by archiving change c-09-padron-ingesta-moodle. Update Purpose after archive.
## Requirements
### Requirement: Degradación controlada de la sincronización Moodle

El sistema SHALL degradar de forma controlada la sincronización contra Moodle Web Services: ante un error del cliente Moodle (p. ej. HTTP 502) o configuración ausente, SHALL responder 502 con una sugerencia de importación manual vía archivo xlsx/csv, sin interrumpir el resto del flujo.

#### Scenario: Moodle responde 502 → sugerir import manual

- **WHEN** el cliente Moodle WS falla con `MoodleWSError(status_code=502)` durante la sincronización
- **THEN** el endpoint responde 502
- **AND** el detalle de la respuesta sugiere usar la importación manual con archivo xlsx/csv

#### Scenario: Moodle WS no configurado

- **WHEN** no hay URL o token de Moodle WS configurados
- **THEN** el endpoint responde 502 indicando que se use la importación manual

#### Scenario: Sincronización automática nocturna fuera de alcance

- **WHEN** se evalúa el alcance de C-09
- **THEN** la sincronización automática nocturna NO se implementa en este change y queda como trabajo futuro

