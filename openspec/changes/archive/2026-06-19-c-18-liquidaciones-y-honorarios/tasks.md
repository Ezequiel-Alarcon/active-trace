## 1. Contexto y Contrato

- [x] 1.1 Leer `AGENTS.md`, `CHANGES.md` C-18, `knowledge-base/04_modelo_de_datos.md` E17-E20, `knowledge-base/05_reglas_de_negocio.md` RN-21/RN-22/RN-31..RN-40, `knowledge-base/06_funcionalidades.md` F10.1..F10.6, `knowledge-base/07_flujos_principales.md` FL-08 y specs de este change.
- [x] 1.2 Relevar modelos reales existentes de `Usuario`, `Materia`, `Asignacion`, comisiones/equipos docentes, RBAC y auditoria para adaptar nombres/campos sin romper capas.
- [x] 1.3 Confirmar que C-18 sigue bajo governance CRITICO y que no se implementan cambios fuera de `liquidaciones`, `facturas`, mapeo Plus, modalidad facturante y permisos necesarios.

## 2. TDD de Dominio Financiero

- [x] 2.1 Escribir tests fallidos para seleccion de `SalarioBase` vigente por rol y periodo, incluyendo ausencia de base vigente.
- [x] 2.2 Escribir tests fallidos para validacion de solapamiento de vigencias en base y plus.
- [x] 2.3 Escribir tests fallidos para Plus acumulado por `N` comisiones activas de la misma clave y materia sin Plus que no suma.
- [x] 2.4 Escribir tests fallidos para total `Base + Plus`, segmentacion general/NEXO/facturante y KPIs `total_sin_factura`/universo facturante.
- [x] 2.5 Escribir tests fallidos para bloqueo de recalculo/cambios sobre periodo cerrado.
- [x] 2.6 Escribir tests fallidos para facturas: registrar pendiente, rechazar no facturante, listar con filtros, marcar abonada con confirmacion y aislar tenants.

## 3. Migracion y Modelos

- [x] 3.1 Crear una migracion Alembic para catalogo fijo/mapeo Plus, `salario_base`, `salario_plus`, `liquidacion`, `factura`, modalidad facturante si falta, permisos `liquidaciones:*`/`facturas:*` y seeds necesarios.
- [x] 3.2 Agregar modelos SQLAlchemy tenant-scoped con soft delete, timestamps, enums, indices y restricciones de unicidad/consulta para liquidaciones, salarios y facturas.
- [x] 3.3 Agregar mapeo opcional de materia a clave Plus fija sin permitir claves custom por tenant.
- [x] 3.4 Agregar modalidad facturante en usuario con default no facturante y sin exponer PII adicional.

## 4. Repositories y Services

- [x] 4.1 Implementar repositories tenant-scoped para salarios base, plus, liquidaciones, facturas y consultas agregadas necesarias desde asignaciones/comisiones/materias.
- [x] 4.2 Implementar service de grilla salarial con validacion de vigencias, claves Plus existentes y permisos esperados.
- [x] 4.3 Implementar service de calculo de liquidaciones por `(cohorte_id, periodo)` aplicando RN-21/RN-34/RN-35/RN-36/RN-37.
- [x] 4.4 Implementar persistencia de snapshots abiertos y bloqueo de recalculo sobre snapshots cerrados.
- [x] 4.5 Implementar service de cierre inmutable con confirmacion explicita y evento de auditoria `LIQUIDACION_CERRAR`.
- [x] 4.6 Implementar service de facturas con estados `Pendiente`/`Abonada`, confirmacion explicita y control de docente facturante.

## 5. Schemas y API

- [x] 5.1 Crear schemas Pydantic v2 para salarios, liquidaciones, KPIs, cierre, exportacion y facturas con `ConfigDict(extra='forbid')`.
- [x] 5.2 Crear endpoints `/api/liquidaciones/*` con guards especificos `liquidaciones:ver`, `liquidaciones:calcular`, `liquidaciones:cerrar`, `liquidaciones:exportar` y `liquidaciones:configurar-salarios`.
- [x] 5.3 Crear endpoints `/api/facturas/*` con guards especificos `facturas:ver`, `facturas:gestionar` y `facturas:descargar`.
- [x] 5.4 Conectar routers al `main_router` sin logica de negocio ni acceso directo a DB.
- [x] 5.5 Asegurar respuestas 403 fail-closed para usuarios sin permisos y 404 para recursos de otros tenants.

## 6. Auditoria, Seguridad y Exportacion

- [x] 6.1 Registrar `LIQUIDACION_CERRAR` con actor, tenant, cohorte, periodo y filas afectadas, sin PII sensible.
- [x] 6.2 Registrar acciones significativas de facturas si el helper de auditoria existente lo soporta sin ampliar alcance innecesario.
- [x] 6.3 Implementar exportacion de vista previa/cerrada preservando segmentacion y totales sin cerrar liquidaciones abiertas.
- [x] 6.4 Verificar que repositories filtran por `tenant_id` por defecto y que identidad/tenant nunca vienen de parametros de request.

## 7. Verificacion

- [x] 7.1 Ejecutar tests backend relevantes de liquidaciones, facturas, grilla salarial, RBAC y modelos afectados usando DB real o contenedor de test, sin mocks de DB.
- [x] 7.2 Ejecutar lint/type checks permitidos por el proyecto para backend sin correr build.
- [x] 7.3 Ejecutar `openspec status --change "c-18-liquidaciones-y-honorarios"` y validar que tasks/specs quedan listos para apply/verify.
- [x] 7.4 Documentar cualquier decision operacional pendiente en el lugar correcto si aparece durante apply, especialmente catalogo inicial exacto de Plus o alcance de HU-49.
