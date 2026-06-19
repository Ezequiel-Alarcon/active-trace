## Why

Los roles FINANZAS y ADMIN actualmente no tienen interfaz dedicada en el SPA. La liquidación de honorarios, gestión de grilla salarial, facturación, estructura académica, administración de usuarios y panel de auditoría existen como APIs de backend pero carecen de vistas frontend. Sin estas pantallas, los usuarios de FINANZAS y ADMIN no pueden operar el sistema. Este change completa la capa de presentación para estos dos roles críticos.

## What Changes

Crear dos feature modules nuevos siguiendo la estructura feature-based existente:

**`features/liquidaciones/`** (FINANZAS):
- Vista de liquidaciones del período con segmentación general / NEXO / factura + KPIs de cabecera (total sin factura, universo facturante)
- Cerrar liquidación (convierte en inmutable)
- Historial de liquidaciones cerradas
- ABM grilla salarial (SalarioBase por rol con vigencia, SalarioPlus con clave/rol/vigencia)
- Gestión de facturas: registrar pendiente, marcar abonada, listar con filtros (docente, estado, rango fechas)

**`features/admin/`** (ADMIN):
- Estructura académica: ABM de carreras, cohortes y materias
- Usuarios del tenant: ABM con roles y asignaciones
- Panel de auditoría y métricas: acciones por día, estado de comunicaciones por docente, interacciones por docente×materia, últimas acciones
- Log completo de auditoría con filtros (rango fechas, materia, usuario, estado)

Actualizaciones transversales:
- Registrar rutas en `shared/router.tsx` con guards `RequirePermission` por cada permiso
- Agregar entradas de navegación condicionales por permiso en `AppLayout.tsx`

## Capabilities

### New Capabilities
- `liquidaciones-periodo`: Vista de liquidaciones del período activo con segmentación general/NEXO/factura y KPIs consolidados. Filtros: cohorte, mes, docente opcional
- `liquidaciones-cierre`: Acción de cierre que inmutabiliza la liquidación del período seleccionado. Solo FINANZAS con permiso `liquidaciones:cerrar`
- `liquidaciones-historial`: Consulta y auditoría de liquidaciones cerradas de períodos anteriores
- `liquidaciones-grilla-salarial`: ABM con vigencia de SalarioBase (por rol) y SalarioPlus (por clave×rol). Permiso `liquidaciones:configurar-salarios`
- `facturas-gestion`: ABM de comprobantes de docentes que facturan. Estados: pendiente/abonada. Filtros: docente, estado, rango fechas
- `estructura-academica`: ABM de carreras, cohortes y materias del catálogo único del tenant. Permiso `estructura:gestionar`
- `usuarios-tenant`: ABM de usuarios del tenant con asignación de roles. Permiso de gestión de usuarios (ADMIN)
- `auditoria-panel`: Dashboard con KPIs de actividad del sistema: acciones/día, comunicaciones por docente, interacciones por docente×materia, últimas N acciones
- `auditoria-log`: Log completo de auditoría con filtros combinados (rango fechas, materia, usuario, estado)

### Modified Capabilities
<!-- No existing frontend capabilities are modified — all are new -->

## Impact

- **Frontend**: dos nuevos feature modules (`liquidaciones/`, `admin/`) con su estructura completa (types, services, hooks, components, pages)
- **Routing**: nuevas rutas protegidas en `shared/router.tsx` bajo el shell autenticado
- **Navegación**: nuevas entradas en `AppLayout.tsx` filtradas por permiso
- **Backend**: consume APIs existentes de C-06 (estructura académica), C-07 (usuarios), C-18 (liquidaciones/facturas), C-19 (auditoría). No requiere cambios en backend
- **Tests**: tests de componente e integración para cada página y hook nuevo, siguiendo patrón de mocks HTTP con `@/test/server`
