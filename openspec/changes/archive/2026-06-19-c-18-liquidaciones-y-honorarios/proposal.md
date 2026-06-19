## Why

Finanzas necesita calcular, revisar, cerrar y auditar honorarios docentes por cohorte y mes con una formula transparente Base + Plus. PA-22/PA-23 ya estan cerradas, asi que el dominio queda desbloqueado: el Plus usa catalogo fijo del programa y se acumula por comision activa sin tope inicial.

## What Changes

- Agrega grilla salarial versionada para `SalarioBase` por rol y `SalarioPlus` por clave fija de Plus y rol, con vigencia temporal abierta.
- Agrega calculo de liquidacion por `(cohorte, periodo)` con detalle por docente, rol, comisiones, base, plus, total, segmento contable y estado `Abierta`/`Cerrada`.
- Agrega cierre inmutable de liquidacion, historial y exportacion de vista previa/cerrada, auditando `LIQUIDACION_CERRAR`.
- Agrega gestion de facturas para docentes facturantes, separando su flujo contable de la liquidacion general Base + Plus.
- Agrega KPIs y segmentacion contable: general sin factura, NEXO visible por separado pero sumado al total, y facturantes excluidos del total liquidable.
- Agrega mapeo opcional de `Materia` a una clave de Plus del catalogo fijo del programa; las instituciones no crean claves propias.
- Agrega permisos `liquidaciones:*` para proteger endpoints de Finanzas con RBAC fail-closed.

## Capabilities

### New Capabilities
- `grilla-salarial`: ABM de salarios base y plus por rol con vigencia temporal y validacion de solapamientos.
- `liquidaciones-calculo`: calculo de liquidaciones por cohorte y periodo aplicando Base + N x Plus por comision activa, con segmentacion contable.
- `liquidaciones-cierre-historial`: cierre inmutable, historial, exportacion y auditoria de liquidaciones.
- `facturas-docentes`: carga, listado, filtros, descarga y marcado de facturas pendientes/abonadas para docentes facturantes.

### Modified Capabilities
- `estructura-academica-materias`: agrega mapeo opcional de materia a clave fija de Plus del programa.
- `usuario-crud`: agrega modalidad de pago/facturante para separar flujo Base+Plus de flujo por factura.
- `rbac-permission-catalogue`: agrega seed de permisos `liquidaciones:ver`, `liquidaciones:calcular`, `liquidaciones:cerrar`, `liquidaciones:exportar`, `liquidaciones:configurar-salarios` y permisos de facturas.

## Impact

- Backend: nuevos modelos, repositorios, services, routers y schemas para `liquidaciones`, `facturas` y grilla salarial, respetando Routers -> Services -> Repositories -> Models.
- Base de datos: migracion para `salario_base`, `salario_plus`, `liquidacion`, `factura` y estructura necesaria para catalogo/mapeo fijo de Plus.
- API: endpoints `/api/liquidaciones/*` y `/api/facturas/*` protegidos con `require_permission(...)` y tenant desde JWT verificado.
- Auditoria: registro de `LIQUIDACION_CERRAR` y acciones significativas de facturas sin exponer PII ni secretos.
- Tests: cobertura de base vigente por periodo, plus acumulado por comisiones activas, total, cierre inmutable, exclusion por factura y segmentacion NEXO/factura/general.
