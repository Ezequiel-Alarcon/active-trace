# comisiones-listado Specification

## Purpose
TBD - created by archiving change c-26-completar-analisis-comisiones-import. Update Purpose after archive.

## Requirements

### Requirement: Listado de comisiones para el usuario autenticado

El sistema SHALL exponer `GET /api/comisiones` que devuelve las comisiones (materia x cohorte) visibles para el usuario autenticado del tenant, en la forma `{ id, materia_id, materia_nombre, cohorte_id, cohorte_nombre }`. Las comisiones SHALL estar scoped por `tenant_id` (tomado de la sesion, nunca de la peticion) y filtradas por soft-delete.

#### Scenario: Devuelve las comisiones del tenant

- **WHEN** un usuario autenticado del tenant solicita `GET /api/comisiones`
- **THEN** el sistema SHALL responder 200 con la lista de comisiones del tenant, cada una con `materia_nombre` y `cohorte_nombre` resueltos

#### Scenario: Aislamiento por tenant

- **WHEN** existen comisiones en otro tenant
- **THEN** la respuesta NO SHALL incluir comisiones que no pertenezcan al `tenant_id` de la sesion

#### Scenario: Sin comisiones configuradas

- **WHEN** el tenant no tiene comisiones
- **THEN** el sistema SHALL responder 200 con una lista vacia (no error)

### Requirement: Identidad y autorizacion desde la sesion

El endpoint SHALL derivar el `tenant_id` y la identidad del JWT verificado, nunca de parametros de la peticion, y SHALL requerir un permiso explicito (fail-closed).

#### Scenario: Sin sesion valida

- **WHEN** se solicita `GET /api/comisiones` sin un token valido
- **THEN** el sistema SHALL responder 401
