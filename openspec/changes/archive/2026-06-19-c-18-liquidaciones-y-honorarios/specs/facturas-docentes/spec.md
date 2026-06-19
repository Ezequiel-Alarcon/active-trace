## ADDED Requirements

### Requirement: Sistema SHALL registrar facturas de docentes facturantes
El sistema SHALL permitir registrar facturas para usuarios docentes con modalidad facturante. Cada factura SHALL incluir docente, periodo `AAAA-MM`, detalle libre, referencia al PDF, tamano de archivo, estado `Pendiente` y fecha de carga.

#### Scenario: Registrar factura pendiente
- **WHEN** se registra una factura para un docente facturante con PDF y detalle valido
- **THEN** el sistema crea `Factura` en estado `Pendiente`
- **AND** persiste `cargada_at`, `referencia_archivo` y `tamano_kb`

#### Scenario: Rechazar factura de docente no facturante
- **WHEN** se intenta registrar una factura para un docente no facturante
- **THEN** el sistema retorna `422 Unprocessable Entity` o `409 Conflict`
- **AND** no crea la factura

### Requirement: Sistema SHALL listar y filtrar facturas para Finanzas
El sistema SHALL exponer listado tenant-scoped de facturas con filtros por docente, estado, rango de fechas y busqueda libre.

#### Scenario: Filtrar facturas pendientes por rango
- **WHEN** FINANZAS llama `GET /api/facturas?estado=Pendiente&desde=2026-06-01&hasta=2026-06-30`
- **THEN** el sistema retorna solo facturas pendientes cargadas en ese rango para el tenant actual

### Requirement: Sistema SHALL marcar factura como abonada con confirmacion
El sistema SHALL permitir a FINANZAS cambiar una factura de `Pendiente` a `Abonada` con confirmacion explicita, registrando `abonada_at`. Una factura abonada SHALL conservarse para historial.

#### Scenario: Marcar factura como abonada
- **WHEN** FINANZAS confirma el pago de una factura pendiente
- **THEN** el sistema cambia el estado a `Abonada`
- **AND** setea `abonada_at`

#### Scenario: Cambio sin confirmacion explicita falla
- **WHEN** FINANZAS intenta marcar una factura como abonada sin confirmacion explicita
- **THEN** el sistema retorna `422 Unprocessable Entity`
- **AND** la factura permanece `Pendiente`

### Requirement: Sistema SHALL permitir descargar archivo de factura
El sistema SHALL permitir descargar o resolver la referencia del PDF de una factura a usuarios con permiso correspondiente, sin exponer archivos de otros tenants.

#### Scenario: Descargar factura del tenant actual
- **WHEN** FINANZAS solicita descargar una factura existente del tenant actual
- **THEN** el sistema entrega el archivo o referencia segura de descarga

#### Scenario: Factura de otro tenant no se revela
- **WHEN** FINANZAS de tenant A solicita una factura de tenant B
- **THEN** el sistema retorna `404 Not Found`
