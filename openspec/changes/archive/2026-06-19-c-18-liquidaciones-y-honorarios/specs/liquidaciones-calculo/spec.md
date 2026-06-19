## ADDED Requirements

### Requirement: Sistema SHALL calcular liquidacion por cohorte y periodo
El sistema SHALL calcular liquidaciones para la unidad `(cohorte_id, periodo)` y tenant actual. Para cada docente/rol alcanzado por asignaciones/comisiones activas del periodo, SHALL calcular `monto_base`, `monto_plus` y `total` segun RN-21/RN-34.

#### Scenario: Calculo crea vista previa abierta
- **WHEN** FINANZAS llama `POST /api/liquidaciones/calcular` con una cohorte y periodo validos
- **THEN** el sistema calcula filas de liquidacion en estado `Abierta`
- **AND** cada fila incluye docente, rol, comisiones, base, plus, total, `es_nexo` y `excluido_por_factura`

### Requirement: Sistema SHALL sumar Plus por comision activa con materia mapeada
El sistema SHALL sumar `Plus(grupo, rol) x N_comisiones`, donde `N_comisiones` es la cantidad de comisiones activas del docente en el periodo cuya materia tiene esa clave fija de Plus. Materias sin clave Plus SHALL aportar cero.

#### Scenario: Dos comisiones de la misma clave acumulan dos veces
- **WHEN** un PROFESOR tiene dos comisiones activas de materias mapeadas a `PROG`
- **AND** `SalarioPlus(PROG, PROFESOR)` vigente vale `25000`
- **THEN** `monto_plus` incluye `50000` por esa clave

#### Scenario: Materia sin clave Plus no suma adicional
- **WHEN** un TUTOR tiene una comision activa de una materia sin clave Plus
- **THEN** esa comision aparece en el detalle
- **AND** no incrementa `monto_plus`

### Requirement: Sistema SHALL segmentar general, NEXO y facturantes
El resultado del calculo SHALL exponer segmentos contables: docentes no facturantes generales, liquidaciones NEXO visibles por separado pero sumadas al total general, y docentes facturantes visibles informativamente pero excluidos del total liquidable.

#### Scenario: NEXO se muestra separado y suma al total
- **WHEN** el calculo incluye una fila con `rol=NEXO`
- **THEN** la respuesta la incluye en el segmento NEXO
- **AND** su `total` se suma al total general sin factura

#### Scenario: Facturante queda excluido del total liquidable
- **WHEN** el calculo incluye un docente con modalidad facturante
- **THEN** su fila tiene `excluido_por_factura=true`
- **AND** su monto no se suma al KPI `total_sin_factura`
- **AND** queda reflejado en el universo facturante para control contable

### Requirement: Sistema SHALL bloquear recalculo de periodo cerrado
El sistema SHALL impedir recalcular o modificar liquidaciones de una cohorte y periodo si ya existen filas cerradas para esa unidad contable.

#### Scenario: Recalculo de periodo cerrado falla
- **WHEN** la cohorte `A` y periodo `2026-06` tienen liquidaciones en estado `Cerrada`
- **AND** FINANZAS intenta calcular nuevamente ese periodo
- **THEN** el sistema retorna `409 Conflict`
- **AND** no modifica ningun snapshot cerrado
