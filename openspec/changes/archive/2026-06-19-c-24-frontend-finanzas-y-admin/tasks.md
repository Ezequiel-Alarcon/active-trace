## 1. Shared — Routing y Navegación

- [x] 1.1 Registrar rutas en `shared/router.tsx`: `/admin/estructura`, `/admin/usuarios`, `/admin/auditoria`, `/admin/auditoria/log`, `/admin/liquidaciones`, `/admin/liquidaciones/historial`, `/admin/liquidaciones/grilla`, `/admin/liquidaciones/facturas` con guards RequirePermission por cada permiso
- [x] 1.2 Agregar entradas condicionales en `AppLayout.tsx` NAV_ITEMS: "Estructura" (`estructura:gestionar`), "Usuarios" (`usuarios:gestionar`), "Auditoría" (`auditoria:ver`), "Liquidaciones" (`liquidaciones:ver`), "Grilla salarial" (`liquidaciones:configurar-salarios`), "Facturas" (`liquidaciones:ver`)
- [x] 1.3 Verificar typecheck (`npx tsc --noEmit`) tras cambios en router y layout

## 2. Feature liquidaciones — Types y Services

- [x] 2.1 Crear `features/liquidaciones/types/liquidaciones.ts` con interfaces: LiquidacionDocenteEntry, LiquidacionPeriodoResponse (segmentada), SalarioBase, SalarioPlus, Factura, LiquidacionHistorialEntry, LiquidacionCierreResponse
- [x] 2.2 Crear `features/liquidaciones/services/liquidacionesApi.ts`: fetchLiquidacionPeriodo, cerrarLiquidacion, fetchHistorial, fetchDetalleHistorial, fetchSalariosBase, createSalarioBase, updateSalarioBase, deleteSalarioBase, fetchSalariosPlus, createSalarioPlus, updateSalarioPlus, deleteSalarioPlus
- [x] 2.3 Crear `features/liquidaciones/services/facturasApi.ts`: fetchFacturas, createFactura, marcarAbonada
- [x] 2.4 Crear hooks TanStack Query en `features/liquidaciones/hooks/useLiquidaciones.ts`: useLiquidacionPeriodo, useCerrarLiquidacion, useHistorial, useDetalleHistorial
- [x] 2.5 Crear hooks en `features/liquidaciones/hooks/useGrillaSalarial.ts`: useSalariosBase, useCreateSalarioBase, useUpdateSalarioBase, useDeleteSalarioBase, useSalariosPlus, useCreateSalarioPlus, useUpdateSalarioPlus, useDeleteSalarioPlus
- [x] 2.6 Crear hooks en `features/liquidaciones/hooks/useFacturas.ts`: useFacturas, useCreateFactura, useMarcarAbonada

## 3. Feature liquidaciones — Componentes y Páginas

- [x] 3.1 Crear `features/liquidaciones/pages/LiquidacionPeriodoPage.tsx`: PageHeader + FilterBar (cohorte, mes, docente) + KpiCards (total_sin_factura, universo_facturante) + tres secciones (General/NEXO/Factura) con DataTable y StatusBadge
- [x] 3.2 Crear `features/liquidaciones/components/CerrarLiquidacionDialog.tsx`: modal de confirmación con Button variant danger, POST al API, manejo de estados success/error
- [x] 3.3 Crear `features/liquidaciones/pages/HistorialPage.tsx`: DataTable de liquidaciones cerradas + navegación a detalle read-only
- [x] 3.4 Crear `features/liquidaciones/pages/GrillaSalarialPage.tsx`: tabs (SalarioBase / Plus), ABM con modales por cada entidad
- [x] 3.5 Crear `features/liquidaciones/components/SalarioBaseFormModal.tsx` y `SalarioPlusFormModal.tsx`: formularios con React Hook Form + Zod
- [x] 3.6 Crear `features/liquidaciones/pages/FacturasPage.tsx`: FilterBar + DataTable + botón "Registrar factura" + acción "Marcar abonada" por fila
- [x] 3.7 Crear `features/liquidaciones/components/FacturaFormModal.tsx` y `MarcarAbonadaDialog.tsx`
- [x] 3.8 Tests: LiquidacionPeriodoPage muestra segmentos, cerrar liquidación confirma y llama API, historial lista vacío, ABM grilla salarial CRUD, facturas filtros y cambio estado

## 4. Feature admin — Estructura Académica

- [x] 4.1 Crear `features/admin/types/estructura.ts` con interfaces: Carrera, Cohorte, Materia (reflect C-06 API responses)
- [x] 4.2 Crear `features/admin/services/estructuraApi.ts`: fetchCarreras, createCarrera, updateCarrera, deleteCarrera, fetchCohortes, createCohorte, updateCohorte, deleteCohorte, fetchMaterias, createMateria, updateMateria, deleteMateria
- [x] 4.3 Crear hooks TanStack Query en `features/admin/hooks/useEstructura.ts`
- [x] 4.4 Crear `features/admin/pages/EstructuraPage.tsx`: tabs (Carreras / Cohortes / Materias) con DataTable + modal ABM por cada entidad
- [x] 4.5 Crear componentes modales: `CarreraFormModal.tsx`, `CohorteFormModal.tsx`, `MateriaFormModal.tsx`
- [x] 4.6 Tests: listado carreras, CRUD con modal, filtro de cohortes por carrera, validación de formularios

## 5. Feature admin — Usuarios del Tenant

- [x] 5.1 Crear `features/admin/types/usuarios.ts` con interfaces: UsuarioTenant, CreateUsuarioRequest, UpdateUsuarioRequest
- [x] 5.2 Crear `features/admin/services/usuariosApi.ts`: fetchUsuarios, createUsuario, updateUsuario, deleteUsuario
- [x] 5.3 Crear hooks en `features/admin/hooks/useUsuarios.ts`
- [x] 5.4 Crear `features/admin/pages/UsuariosPage.tsx`: FilterBar con búsqueda + DataTable + modales crear/editar + confirmación eliminar
- [x] 5.5 Crear `features/admin/components/UsuarioFormModal.tsx` con React Hook Form + Zod (campos: nombre, apellidos, email, dni, cuil, roles multi-select)
- [x] 5.6 Tests: listado con búsqueda, crear usuario valida email único, eliminar con confirmación

## 6. Feature admin — Auditoría y Log

- [x] 6.1 Crear `features/admin/types/auditoria.ts` con interfaces: ActionsPerDayEntry, ComunicacionStatusEntry, InteraccionEntry, AuditLogEntry, AuditLogResponse
- [x] 6.2 Crear `features/admin/services/auditoriaApi.ts`: fetchActionsPerDay, fetchComunicacionStatus, fetchInteractions, fetchLastActions, fetchAuditLog
- [x] 6.3 Crear hooks en `features/admin/hooks/useAuditoria.ts`: useActionsPerDay, useComunicacionStatus, useInteractions, useLastActions, useAuditLog
- [x] 6.4 Crear `features/admin/pages/AuditoriaPanelPage.tsx`: FilterBar + secciones: acciones/día (chart simple), comunicaciones (DataTable), interacciones (DataTable), últimas acciones (DataTable compacta)
- [x] 6.5 Crear `features/admin/pages/AuditoriaLogPage.tsx`: FilterBar con rango fechas + materia + usuario + estado, DataTable paginada del log completo
- [x] 6.6 Tests: panel carga KPIs, log muestra paginación, filtros combinados, loading/error states

## 7. Integración y verificación final

- [x] 7.1 Verificar que todas las rutas nuevas funcionan con guards de permiso (navegar sin permiso → Forbidden403)
- [x] 7.2 Verificar navegación lateral muestra entradas solo para permisos habilitados
- [x] 7.3 Correr suite completa de tests (`npm test`) y typecheck (`npx tsc --noEmit`)
- [x] 7.4 Verificar cobertura (≥80% líneas en código nuevo)
