## ADDED Requirements

### Requirement: Permission catalogue SHALL seed liquidaciones and facturas permissions
El sistema SHALL sembrar permisos tenant-scoped necesarios para C-18, incluyendo `liquidaciones:ver`, `liquidaciones:calcular`, `liquidaciones:cerrar`, `liquidaciones:exportar`, `liquidaciones:configurar-salarios`, `facturas:ver`, `facturas:gestionar` y `facturas:descargar`, sin duplicar permisos existentes.

#### Scenario: Migration seeds liquidaciones permissions
- **WHEN** la migracion de C-18 corre en una instalacion sin permisos de liquidaciones
- **THEN** inserta los permisos `liquidaciones:*` requeridos
- **AND** los asigna al rol FINANZAS segun matriz base

#### Scenario: Migration does not duplicate permissions
- **WHEN** un permiso `liquidaciones:ver` ya existe para el tenant/catalogo correspondiente
- **THEN** la migracion no crea duplicados

### Requirement: API endpoints SHALL require fine-grained liquidaciones permissions
Todo endpoint de `/api/liquidaciones/*` y `/api/facturas/*` SHALL declarar `require_permission(...)` con el permiso especifico de la accion. Sin permiso explicito, el sistema SHALL responder 403.

#### Scenario: Usuario sin permiso no ve liquidaciones
- **WHEN** un usuario autenticado sin `liquidaciones:ver` llama `GET /api/liquidaciones`
- **THEN** el sistema retorna `403 Forbidden`

#### Scenario: FINANZAS puede cerrar liquidacion
- **WHEN** un usuario FINANZAS con `liquidaciones:cerrar` confirma el cierre de una liquidacion
- **THEN** el guard autoriza la solicitud y el service procesa la accion
