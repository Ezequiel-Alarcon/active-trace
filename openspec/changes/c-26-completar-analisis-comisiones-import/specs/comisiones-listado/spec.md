## ADDED Requirements

### Requirement: Listado de comisiones para el usuario autenticado

El sistema SHALL exponer `GET /api/comisiones` que devuelve las comisiones (materia × cohorte) visibles para el usuario autenticado del tenant, en la forma `{ id, materia_id, materia_nombre, cohorte_id, cohorte_nombre }`. Las comisiones SHALL estar scoped por `tenant_id` (tomado de la sesión, nunca de la petición) y filtradas por soft-delete.

#### Scenario: Devuelve las comisiones del tenant

- **WHEN** un usuario autenticado del tenant solicita `GET /api/comisiones`
- **THEN** el sistema SHALL responder 200 con la lista de comisiones del tenant, cada una con `materia_nombre` y `cohorte_nombre` resueltos

#### Scenario: Aislamiento por tenant

- **WHEN** existen comisiones en otro tenant
- **THEN** la respuesta NO SHALL incluir comisiones que no pertenezcan al `tenant_id` de la sesión

#### Scenario: Sin comisiones configuradas

- **WHEN** el tenant no tiene comisiones
- **THEN** el sistema SHALL responder 200 con una lista vacía (no error)

### Requirement: Identidad y autorización desde la sesión

El endpoint SHALL derivar el `tenant_id` y la identidad del JWT verificado, nunca de parámetros de la petición, y SHALL requerir un permiso explícito (fail-closed).

#### Scenario: Sin sesión válida

- **WHEN** se solicita `GET /api/comisiones` sin un token válido
- **THEN** el sistema SHALL responder 401
