import { Suspense } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { useAuth } from '@/features/auth/components/AuthProvider';
import { useLogout } from '@/features/auth/hooks/useLogout';
import { usePerfil } from '@/features/perfil/hooks/usePerfil';

interface NavItem {
  label: string;
  to: string;
  permission?: string; // undefined = visible to all authenticated users
}

interface NavSection {
  label: string;
  items: NavItem[];
  /** Permission required to see the entire section (header + children). */
  sectionPermission?: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Inicio', to: '/' },
  { label: 'Comisión', to: '/comision', permission: 'analisis:ver' },
  { label: 'Monitor', to: '/monitor', permission: 'analisis:ver' },
  { label: 'Comunicaciones', to: '/comision/comunicar', permission: 'comunicacion:enviar' },
  { label: 'Aprobaciones', to: '/comision/aprobaciones', permission: 'comunicacion:aprobar' },
  { label: 'Mi Perfil', to: '/perfil' },
];

const LIQUIDACIONES_SECTION: NavSection = {
  label: 'Liquidaciones',
  items: [
    { label: 'Periodo', to: '/admin/liquidaciones/periodo', permission: 'liquidaciones:ver' },
    { label: 'Historial', to: '/admin/liquidaciones/historial', permission: 'liquidaciones:ver' },
    { label: 'Grilla salarial', to: '/admin/liquidaciones/grilla', permission: 'liquidaciones:configurar-salarios' },
    { label: 'Facturas', to: '/admin/liquidaciones/facturas', permission: 'liquidaciones:ver' },
  ],
};

const ADMIN_SECTION: NavSection = {
  label: 'Administración',
  items: [
    { label: 'Estructura', to: '/admin/estructura', permission: 'estructura:gestionar' },
    { label: 'Usuarios', to: '/admin/usuarios', permission: 'usuarios:gestionar' },
    { label: 'Auditoría', to: '/admin/auditoria', permission: 'auditoria:ver' },
    { label: 'Auditoría log', to: '/admin/auditoria/log', permission: 'auditoria:ver' },
  ],
};

const PROFESOR_SECTION: NavSection = {
  label: 'Profesor',
  items: [
    { label: 'Mis Guardias', to: '/profesor/guardias', permission: 'encuentros:registrar_guardia' },
    { label: 'Mensajes', to: '/profesor/mensajes', permission: 'mensajes:ver' },
    { label: 'Mis Equipos', to: '/profesor/equipos', permission: 'equipos:ver' },
    { label: 'Coloquios', to: '/coordinacion/coloquios', permission: 'coloquios:ver' },
  ],
};

const TUTOR_SECTION: NavSection = {
  label: 'Tutor',
  items: [
    { label: 'Atrasados', to: '/comision/atrasados', permission: 'atrasados:ver' },
    { label: 'Entregas', to: '/comision/entregas', permission: 'entregas:ver_sin_corregir' },
    { label: 'Mis Guardias', to: '/profesor/guardias', permission: 'encuentros:registrar_guardia' },
    { label: 'Mensajes', to: '/profesor/mensajes', permission: 'mensajes:ver' },
    { label: 'Mis Equipos', to: '/profesor/equipos', permission: 'equipos:ver' },
  ],
};

const ALUMNO_SECTION: NavSection = {
  label: 'Mi Espacio',
  items: [
    { label: 'Mi Academia', to: '/alumno/academia', permission: 'academico:ver_estado_propio' },
    { label: 'Mis Reservas', to: '/alumno/reservas', permission: 'coloquios:reservar' },
    { label: 'Mensajes', to: '/profesor/mensajes', permission: 'mensajes:ver' },
  ],
};

const COORDINACION_SECTION: NavSection = {
  label: 'Coordinación',
  items: [
    { label: 'Equipos', to: '/coordinacion/equipos', permission: 'equipos:asignar' },
    { label: 'Avisos', to: '/coordinacion/avisos', permission: 'avisos:publicar' },
    { label: 'Tareas', to: '/coordinacion/tareas', permission: 'tareas:gestionar' },
    { label: 'Monitor', to: '/coordinacion/monitor', permission: 'equipos:asignar' },
    { label: 'Encuentros', to: '/coordinacion/encuentros', permission: 'encuentros:gestionar' },
    { label: 'Coloquios', to: '/coordinacion/coloquios', permission: 'coloquios:ver' },
    { label: 'Setup Cuatrimestre', to: '/coordinacion/setup', permission: 'estructura:gestionar' },
  ],
};

export default function AppLayout() {
  const { hasPermission } = useAuth();
  const logout = useLogout();
  const { data: perfil } = usePerfil();

  const displayName = perfil
    ? `${perfil.nombre} ${perfil.apellidos}`.trim()
    : null;

  const visibleItems = NAV_ITEMS.filter(
    (item) => !item.permission || hasPermission(item.permission),
  );

  const visibleProfesorItems = PROFESOR_SECTION.items.filter(
    (item) => !item.permission || hasPermission(item.permission),
  );

  const visibleTutorItems = TUTOR_SECTION.items.filter(
    (item) => !item.permission || hasPermission(item.permission),
  );

  const visibleAlumnoItems = ALUMNO_SECTION.items.filter(
    (item) => !item.permission || hasPermission(item.permission),
  );

  const visibleCoordinacionItems = COORDINACION_SECTION.items.filter(
    (item) => !item.permission || hasPermission(item.permission),
  );

  const visibleLiquidacionesItems = LIQUIDACIONES_SECTION.items.filter(
    (item) => !item.permission || hasPermission(item.permission),
  );
  const visibleAdminItems = ADMIN_SECTION.items.filter(
    (item) => !item.permission || hasPermission(item.permission),
  );

  const showLiquidaciones = visibleLiquidacionesItems.length > 0;
  const showAdmin = visibleAdminItems.length > 0;
  const showCoordinacion = visibleCoordinacionItems.length > 0;
  // PROFESOR: tiene calificaciones:ver pero no es ADMIN (estructura:gestionar)
  const showProfesor = hasPermission('calificaciones:ver') && !hasPermission('estructura:gestionar');
  // TUTOR: tiene atrasados:ver pero no calificaciones:ver (PROFESOR) ni equipos:asignar (COORDINADOR)
  const showTutor = hasPermission('atrasados:ver') && !hasPermission('calificaciones:ver') && !hasPermission('equipos:asignar');
  // ALUMNO: único con academico:ver_estado_propio
  const showAlumno = hasPermission('academico:ver_estado_propio');

  // ── Shared nav item class builder ──────────────────────────────────────
  const navItemClass = (isActive: boolean) =>
    `flex items-center pl-4 pr-4 py-2.5 text-sm transition-colors border-l-2 ${
      isActive
        ? 'border-blue-400 bg-slate-800 text-white font-medium'
        : 'border-transparent text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
    }`;

  const sectionLabel = (label: string) => (
    <span className="px-4 pt-5 pb-1 block text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
      {label}
    </span>
  );

  const renderItems = (items: NavItem[]) =>
    items.map((item) => (
      <NavLink key={item.to} to={item.to} end className={({ isActive }) => navItemClass(isActive)}>
        {item.label}
      </NavLink>
    ));

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Header: dark chrome ─────────────────────────────────────────── */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <span className="flex h-5 w-2 flex-col gap-0.5" aria-hidden="true">
            <span className="flex-1 rounded-sm bg-blue-400" />
            <span className="flex-1 rounded-sm bg-blue-600" />
          </span>
          <span className="font-semibold text-white tracking-tight text-[15px]">active trace</span>
        </div>
        <div className="flex items-center gap-5">
          {displayName && (
            <span className="text-sm text-slate-400">{displayName}</span>
          )}
          <button
            type="button"
            onClick={logout}
            className="text-sm text-slate-500 hover:text-red-400 transition-colors"
          >
            Cerrar sesión
          </button>
        </div>
      </header>

      <div className="flex flex-1">
        {/* ── Sidebar: dark nav ───────────────────────────────────────────── */}
        <nav
          aria-label="Navegación principal"
          className="w-56 bg-slate-900 border-r border-slate-800 py-2 flex flex-col"
        >
          {renderItems(visibleItems)}

          {showProfesor && (
            <>
              {sectionLabel(PROFESOR_SECTION.label)}
              {renderItems(visibleProfesorItems)}
            </>
          )}

          {showTutor && (
            <>
              {sectionLabel(TUTOR_SECTION.label)}
              {renderItems(visibleTutorItems)}
            </>
          )}

          {showAlumno && (
            <>
              {sectionLabel(ALUMNO_SECTION.label)}
              {renderItems(visibleAlumnoItems)}
            </>
          )}

          {showLiquidaciones && (
            <>
              {sectionLabel(LIQUIDACIONES_SECTION.label)}
              {renderItems(visibleLiquidacionesItems)}
            </>
          )}

          {showAdmin && (
            <>
              {sectionLabel(ADMIN_SECTION.label)}
              {renderItems(visibleAdminItems)}
            </>
          )}

          {showCoordinacion && (
            <>
              {sectionLabel(COORDINACION_SECTION.label)}
              {renderItems(visibleCoordinacionItems)}
            </>
          )}
        </nav>

        {/* ── Main content ────────────────────────────────────────────────── */}
        <main className="flex-1 p-8 bg-slate-50 min-h-0">
          <Suspense fallback={<p className="text-sm text-slate-500">Cargando…</p>}>
            <Outlet />
          </Suspense>
        </main>
      </div>
    </div>
  );
}
