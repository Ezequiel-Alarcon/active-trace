## ADDED Requirements

### Requirement: Selección de comisión (materia + cohorte)

El sistema SHALL proveer una vista de gestión de comisión donde el PROFESOR selecciona la materia y la cohorte que quiere analizar. Las opciones disponibles MUST limitarse a las comisiones a las que la sesión autenticada tiene acceso; la identidad, tenant y permisos se resuelven exclusivamente desde la sesión, nunca desde parámetros de la petición. Mientras no haya una comisión seleccionada, las vistas de análisis MUST mostrar un estado guía que invite a seleccionar materia y cohorte.

#### Scenario: El profesor selecciona materia y cohorte

- **WHEN** el PROFESOR abre la gestión de comisión y elige una materia y una cohorte de las opciones de su sesión
- **THEN** la selección queda activa y las vistas de análisis (atrasados, ranking, notas finales, reportes) se cargan para esa comisión

#### Scenario: Sin comisión seleccionada se muestra un estado guía

- **WHEN** el PROFESOR entra a la gestión de comisión sin haber seleccionado materia/cohorte
- **THEN** se renderiza un estado guía que pide seleccionar materia y cohorte
- **AND** no se dispara ninguna consulta de análisis hasta que la selección exista

### Requirement: Navegación entre vistas de análisis de la comisión

El sistema SHALL ofrecer navegación entre las vistas de la comisión seleccionada (importación, atrasados, ranking, notas finales, reportes rápidos, entregas sin corregir, comunicación). La comisión activa MUST conservarse al cambiar de vista sin requerir reselección.

#### Scenario: Cambio de vista conserva la comisión activa

- **WHEN** el PROFESOR tiene una comisión seleccionada y navega de la vista de atrasados a la de ranking
- **THEN** la nueva vista se renderiza para la misma comisión sin pedir reselección de materia/cohorte

### Requirement: Rutas y menú protegidos por permiso

El sistema SHALL registrar las rutas de la feature dentro del shell autenticado, cada una envuelta en `RequirePermission` con su permiso `modulo:accion`. Las entradas de menú correspondientes MUST renderizarse solo si la sesión incluye el permiso requerido (fail-closed). La ruta de importación usa `calificaciones:importar`; las vistas de análisis y monitor usan `atrasados:ver`; la comunicación usa `comunicacion:enviar`.

#### Scenario: La ruta de importación se bloquea sin el permiso

- **WHEN** un usuario autenticado cuyas permisos efectivos NO incluyen `calificaciones:importar` navega a la ruta de importación
- **THEN** se renderiza la página `Forbidden403`
- **AND** el contenido de la importación no se renderiza

#### Scenario: El menú oculta las vistas que la sesión no puede usar

- **WHEN** la sesión incluye `atrasados:ver` pero no `comunicacion:enviar`
- **THEN** el menú muestra las entradas de análisis guardadas por `atrasados:ver`
- **AND** el menú no muestra la entrada de comunicación guardada por `comunicacion:enviar`
