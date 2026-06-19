## 1. Tokens y colores semánticos

- [x] 1.1 Crear `frontend/src/shared/ui/estado-colores.ts` con el mapa `estado → clases` (atrasado/fallido=rojo, aprobado/enviado=verde, pendiente/cancelado=ámbar, en-envio/acento=azul, neutro/pendiente-cola=gris) — TDD: test que verifica que cada estado resuelve a su set de clases
- [x] 1.2 Definir tokens visuales (acento `blue-600`, neutros, espaciado) — decisión: sin extender `tailwind.config` (utilidades estándar de Tailwind); los tokens de estado viven en `estado-colores.ts`
- [x] 1.3 Crear barrel export inicial `frontend/src/shared/ui/index.ts`

## 2. Primitivos UI (Strict TDD: RED → GREEN → triangular → refactor)

- [x] 2.1 `Button` (variantes primary/secondary/danger + disabled) con tests
- [x] 2.2 `Badge` genérico con tests
- [x] 2.3 `StatusBadge` que consume `estado-colores.ts` con tests (atraso, estados de cola)
- [x] 2.4 `Card` (contenedor borde+padding) con tests
- [x] 2.5 `PageHeader` (título + slot de acciones) con tests
- [x] 2.6 `EmptyState` (mensaje gris, `role="status"`) con tests
- [x] 2.7 `KpiCard` (número grande + etiqueta) con tests
- [x] 2.8 `FilterBar` (contenedor de filtros horizontal) con tests
- [x] 2.9 `DataTable<T>` genérico tipado (columnas render-prop, selección opcional, estado vacío → `EmptyState`) con tests
- [x] 2.10 Exportar todos los primitivos desde `@/shared/ui` (barrel) y verificar import único

## 3. Re-estilar el shell

- [x] 3.1 Re-estilar `AppLayout.tsx` con la capa UI preservando header (marca, email desde sesión, cerrar sesión) y sidebar (nav filtrada por permiso, fail-closed)
- [x] 3.2 Correr `AppLayout.test.tsx` y confirmar que pasa sin regresión (identidad y permisos intactos)

## 4. Re-estilar páginas — riesgo bajo

- [x] 4.1 `LoginPage` (+ Forgot/Reset) usando `Card`, `Button`, `TextField` (nuevo primitivo: label+input+error, forwardRef RHF-compatible)
- [x] 4.2 `ImportarCalificacionesForm` / page: `Button` + `Card`, preservando labels/textos/roles que asertan los tests
- [x] 4.3 Correr tests de auth y calificaciones; confirmar sin regresión (140/140 verde)

## 5. Re-estilar páginas — tablas

- [x] 5.1 `TablaAtrasados` con `DataTable` + `StatusBadge` (rojo) + `Button` "Comunicar seleccionados"
- [x] 5.2 `RankingVista` con `DataTable` + badge verde de aprobadas
- [x] 5.3 `NotasFinalesVista` con `DataTable` (vista por materia: Materia/Alumnos/Aprobados/Tasa/Promedio; sin Exportar porque el componente no tiene esa lógica)
- [x] 5.4 `EntregasSinCorregir` con `DataTable` + `StatusBadge` ámbar "Sin corregir" + `Button` (Cruzar / Exportar CSV)
- [x] 5.5 `ReportesVista` — se mantiene como estado informativo (placeholder): no trae datos hasta resolver el mapping comisión→materia (TODO backend); KpiCards sin datos sería fake
- [x] 5.6 `MonitorSeguimiento` con `FilterBar` + `DataTable` + `Button`. Extensión: `DataTable.rowKey` ahora recibe `(row, index)` para claves estables con ids nulos/duplicados
- [x] 5.7 Correr tests de analisis/entregas/monitor; confirmar sin regresión (141/141 verde)

## 6. Re-estilar páginas — flujos compuestos

- [x] 6.1 `ComisionPage` workspace: `PageHeader` + tabs con transición (sin control de umbral: vive en el form de importar, no en la page)
- [x] 6.2 Flujo Comunicar (multi-step): `SeleccionDestinatarios`/`PreviewComunicacion`/`TrackingComunicacion` con `Card` + `Button`s; tracking con `StatusBadge` de cola gris/azul/verde/rojo/ámbar (corregido En envío→azul, Cancelado→ámbar según spec)
- [x] 6.3 Correr tests de comision/comunicacion; confirmar sin regresión (141/141 verde)

## 7. Verificación final

- [x] 7.1 Correr la suite completa del frontend — 141/141 verde (cero regresión). Typecheck: solo el error pre-existente de AuthProvider (refresh_token), no introducido por C-25
- [x] 7.2 Auditoría OK: 0 badges de estado ad-hoc en features (todos vía `StatusBadge`), 0 estilos inline, 0 `any`, ningún componente >200 LOC (primitivos máx 80; ImportarCalificacionesForm 196)
- [x] 7.3 Cobertura de primitivos `shared/ui` = 100% (stmts/branch/funcs/lines) — supera ≥80%. Agregado `src/shared/ui/**` a `coverage.include`. NOTA: threshold global (80%) falla por deuda PRE-EXISTENTE (LoginForm/Forgot/Reset forms y pages de auth = 0%, nunca tuvieron tests; fuera del scope de C-25)
