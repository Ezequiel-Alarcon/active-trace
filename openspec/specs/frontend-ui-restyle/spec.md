# frontend-ui-restyle Specification

## Purpose
TBD - created by archiving change c-25-frontend-design-system. Update Purpose after archive.
## Requirements
### Requirement: El shell de la aplicación adopta el design system

El `AppLayout` SHALL re-estilarse usando los componentes y tokens del design system, preservando exactamente su comportamiento actual: el header SHALL mostrar la marca "Active Trace", el email del usuario obtenido de la sesión y la acción "Cerrar sesión"; el sidebar SHALL listar los ítems de navegación filtrados por permiso (fail-closed). El restyle NO SHALL alterar la lógica de identidad ni el filtrado de permisos.

#### Scenario: Identidad y permisos preservados tras el restyle

- **WHEN** un usuario sin el permiso `analisis:ver` carga el shell re-estilado
- **THEN** el ítem "Monitor" NO SHALL aparecer en el sidebar (mismo comportamiento fail-closed que antes del restyle)

#### Scenario: El email proviene de la sesión

- **WHEN** se renderiza el header re-estilado
- **THEN** el email mostrado SHALL provenir de `session.user.email` y NO de ningún parámetro de la URL o entrada del usuario

### Requirement: Las 10 páginas core adoptan el design system sin regresión funcional

Las 10 páginas core (login, importar calificaciones, comisión workspace, atrasados, ranking, notas finales, reportes, entregas sin corregir, comunicaciones, monitor) SHALL re-estilarse consumiendo los componentes de `@/shared/ui`, sin modificar sus hooks de datos (TanStack Query), su lógica de pasos ni sus contratos de props de datos. Los tests existentes de cada página SHALL seguir pasando.

#### Scenario: Restyle preserva los tests existentes

- **WHEN** se ejecuta la suite de tests del frontend tras re-estilar una página
- **THEN** todos los tests que pasaban antes del restyle SHALL seguir pasando

#### Scenario: Estados de carga, error y vacío conservados

- **WHEN** una página re-estilada está cargando, en error, o sin datos
- **THEN** SHALL seguir mostrando un estado de carga, de error (`role="alert"`) y vacío (`EmptyState`) respectivamente, equivalentes a los previos

### Requirement: Colores semánticos de estado consistentes entre vistas

Las vistas que muestran estados (atrasados, ranking, notas finales, entregas sin corregir, comunicaciones, monitor) SHALL usar `StatusBadge` con los colores semánticos centralizados, de modo que un mismo estado se vea idéntico en todas las pantallas.

#### Scenario: Estado "atrasado" idéntico en todas las vistas

- **WHEN** el estado `atrasado` aparece en la tabla de atrasados y en el monitor
- **THEN** SHALL renderizarse con el mismo color rojo en ambas vistas

#### Scenario: Estados de cola de comunicaciones

- **WHEN** la vista de comunicaciones muestra los estados Pendiente, En envío, Enviado, Fallido y Cancelado
- **THEN** cada uno SHALL usar su color semántico centralizado (gris, azul, verde, rojo, ámbar)
