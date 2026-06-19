# frontend-app-shell — Delta Spec

## MODIFIED Requirements

### Requirement: An authenticated layout wraps protected routes and hosts the permission-aware menu

#### ADDED Scenario: Sidebar muestra sección de Coordinación para roles con permisos

- **WHEN** un usuario autenticado tiene permisos de COORDINADOR o ADMIN
- **THEN** el sidebar SHALL mostrar una sección "Coordinación" con sub-ítems: Equipos, Avisos, Tareas, Monitor, Encuentros, Coloquios, Setup de Cuatrimestre
- **AND** cada sub-ítem SHALL filtrarse por permiso (fail-closed: sin permiso → no se muestra)

#### ADDED Scenario: Rutas de coordinación registradas en el router

- **WHEN** el enrutador se inicializa
- **THEN** SHALL existir rutas protegidas por permiso para:
  - /coordinacion/equipos (permiso equipos:asignar)
  - /coordinacion/avisos (permiso avisos:publicar)
  - /coordinacion/tareas (permiso tareas:ver)
  - /coordinacion/monitor (permiso analisis:ver)
  - /coordinacion/encuentros (permiso encuentros:ver)
  - /coordinacion/coloquios (permiso coloquios:ver)
  - /coordinacion/setup (permiso estructura:gestionar)
- **AND** cada ruta SHALL cargar su página mediante React.lazy

#### ADDED Scenario: Ruta /coordinacion redirige a equipos

- **WHEN** un usuario navega a /coordinacion
- **THEN** el sistema SHALL redirigir a /coordinacion/equipos
