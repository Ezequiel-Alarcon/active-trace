## Context

C-18 incorpora el dominio financiero de honorarios docentes sobre la base ya archivada de tenants, RBAC, usuarios/asignaciones y estructura academica. El dominio es CRITICO porque toca liquidaciones, auditoria, permisos y datos sensibles de docentes.

La fuente de verdad funcional queda definida por E17-E20, RN-21/RN-22/RN-31..RN-40, F10.1..F10.6, FL-08, HU-39..HU-41 y HU-48..HU-49. PA-22/PA-23 estan cerradas: las claves de Plus son catalogo fijo del programa/sistema, cada materia puede mapear a una clave existente o quedar sin Plus, y el Plus se acumula por comision activa sin tope inicial para PROFESOR, TUTOR, COORDINADOR y NEXO.

La implementacion debe respetar las reglas duras existentes: identidad y tenant desde JWT, repositories con scope de tenant por defecto, RBAC fail-closed, logica de negocio fuera de routers, queries solo en repositories, Pydantic v2 con `extra='forbid'`, soft delete y auditoria para acciones significativas.

## Goals / Non-Goals

**Goals:**
- Modelar `SalarioBase`, `SalarioPlus`, `Liquidacion` y `Factura` con tenant, soft delete, timestamps y restricciones de integridad.
- Calcular liquidaciones por `(cohorte, periodo)` usando base vigente por rol y `N x Plus(clave, rol)` por comisiones activas cuya materia tenga clave de Plus.
- Persistir liquidaciones abiertas/cerradas con snapshot de montos, comisiones y flags contables para que el cierre sea inmutable.
- Exponer APIs `/api/liquidaciones/*` y `/api/facturas/*` con permisos `liquidaciones:*` y `facturas:*`.
- Separar contablemente docentes no facturantes, NEXO y facturantes, con KPIs de cabecera.
- Permitir ABM de grilla salarial y gestion de facturas sin permitir claves Plus custom por tenant.

**Non-Goals:**
- No implementar frontend de finanzas; queda para C-24.
- No integrar pagos bancarios ni conciliacion automatica.
- No validar montos de factura contra una liquidacion equivalente; HU-49 conserva criterios pendientes fuera de este change.
- No introducir topes de Plus; cualquier tope futuro debe ser regla versionada nueva.
- No cambiar el modelo de permisos base ni el mecanismo JWT/RBAC existente.

## Decisions

### Decision 1: Catalogo fijo de Plus separado del valor configurable

Crear una estructura de catalogo fijo para claves de Plus, por ejemplo `plus_categoria` sin administracion por tenant, y referenciarla desde `Materia.plus_grupo`/`plus_categoria_id` y desde `SalarioPlus`. Los montos siguen siendo tenant-scoped en `salario_plus`.

Rationale: separa la taxonomia de programa, comun a instituciones, del valor monetario configurable por tenant y vigencia. Evita que cada institucion invente claves incompatibles y hace testeable RN-33/RN-34.

Alternativa considerada: guardar `grupo` como texto libre en `Materia` y `SalarioPlus`. Se descarta porque permitiria errores tipograficos y claves de facto por institucion.

### Decision 2: Snapshot de liquidacion por fila docente/rol al calcular y cerrar

Persistir una fila `Liquidacion` por docente, rol, cohorte y periodo, con `monto_base`, `monto_plus`, `total`, `comisiones`, `es_nexo`, `excluido_por_factura` y `estado`. El calculo puede regenerar filas abiertas del periodo, pero nunca modifica filas cerradas.

Rationale: el snapshot conserva la formula aplicada al momento del cierre y permite historial/auditoria aunque cambie la grilla salarial o asignaciones futuras.

Alternativa considerada: calcular siempre on-demand desde asignaciones y grilla. Se descarta porque rompe RN-22: un cambio retroactivo en grilla/asignacion alteraria historicos cerrados.

### Decision 3: Unidad de cierre `(tenant_id, cohorte_id, periodo)`

El cierre opera sobre todas las filas de liquidacion abiertas para una cohorte y periodo. Debe existir una restriccion que impida duplicar liquidacion cerrada para el mismo docente/rol/cohorte/periodo y que bloquee recalculo sobre periodos cerrados.

Rationale: RN-37 define la unidad contable. Cerrar por docente generaria estados parciales dificiles de auditar para Finanzas.

Alternativa considerada: cierre global mensual por tenant. Se descarta porque distintas cohortes tienen liquidaciones independientes.

### Decision 4: Facturantes visibles pero excluidos del total liquidable

El calculo puede incluir docentes facturantes como filas informativas con `excluido_por_factura=true`, pero los KPIs y export deben diferenciar `total_sin_factura` del universo facturante. Las facturas son el flujo operativo de pago para esos docentes.

Rationale: Finanzas necesita visibilidad completa sin mezclar obligaciones contables. Cumple RN-35/RN-38.

Alternativa considerada: omitir facturantes de la liquidacion. Se descarta porque reduce trazabilidad y dificulta comparar universo docente completo.

### Decision 5: Repositories agregados para calculo, service para reglas

Los repositories exponen consultas tenant-scoped para asignaciones vigentes, comisiones activas, materias con Plus, salarios vigentes, liquidaciones y facturas. El service orquesta RN-21/RN-34/RN-35/RN-36/RN-37, arma snapshots y valida cierre.

Rationale: mantiene queries fuera de services y reglas fuera de routers, sin convertir SQL en logica de negocio opaca.

Alternativa considerada: query SQL monolitica que devuelva todo calculado. Se descarta porque mezcla persistencia con reglas y complica tests unitarios de negocio.

## Risks / Trade-offs

- [Risk] El modelo actual de `Materia` puede no tener campo Plus ni entidad de catalogo. -> Mitigacion: incluir migracion y delta spec de `estructura-academica-materias` para mapeo opcional a clave fija.
- [Risk] El modelo actual de `Usuario` puede no tener modalidad facturante. -> Mitigacion: incluir delta spec de `usuario-crud` y migracion con default no facturante para no cambiar comportamiento existente.
- [Risk] Asignaciones y comisiones activas pueden tener nombres/estructuras ya existentes con matices. -> Mitigacion: en apply, leer modelos reales de C-07/C-08 y escribir tests de integracion antes de implementar calculo.
- [Risk] Recalcular periodos abiertos puede pisar ediciones manuales si existieran. -> Mitigacion: no introducir edicion manual de montos en C-18; los montos derivan de grilla/asignaciones hasta el cierre.
- [Risk] Archivos PDF de facturas requieren almacenamiento. -> Mitigacion: persistir referencia de archivo y metadatos; el mecanismo fisico de storage puede reutilizar el patron existente del proyecto o quedar como adaptador interno sin servicio externo nuevo.

## Migration Plan

1. Crear migracion Alembic unica para el schema de C-18: catalogo/mapeo Plus, `salario_base`, `salario_plus`, `liquidacion`, `factura`, campos de usuario facturante si faltan y permisos nuevos.
2. Sembrar catalogo fijo inicial de claves Plus del programa con `ON CONFLICT DO NOTHING`.
3. Agregar indices y restricciones: unicidad tenant-scoped, no solapamiento de vigencias por rol/grupo cuando sea viable, busquedas por `(tenant_id, cohorte_id, periodo)`, facturas por `(tenant_id, usuario_id, periodo)`.
4. Deploy con defaults seguros: usuarios existentes no facturantes, materias existentes sin clave Plus, salarios sin registros hasta que Finanzas configure grilla.
5. Rollback: remover tablas/campos nuevos y seeds de permisos/catalogo si no hay liquidaciones cerradas en produccion; si existen cierres, rollback requiere decision operativa porque son registros contables auditables.

## Open Questions

- HU-49 mantiene criterios pendientes para la pantalla docente de carga y notificaciones; C-18 cubre API/flujo backend de facturas, no la experiencia frontend docente.
- El listado exacto de claves del catalogo fijo de Plus debe venir del programa antes de cargar datos reales; la estructura queda preparada y la migracion puede sembrar valores iniciales acordados.
