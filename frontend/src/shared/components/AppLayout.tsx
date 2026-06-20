import { Suspense } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { useAuth } from '@/features/auth/components/AuthProvider';
import { useLogout } from '@/features/auth/hooks/useLogout';

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
  const { hasPermission, session } = useAuth();
  const logout = useLogout();

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

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="h-5 w-5 rounded bg-blue-600" aria-hidden="true" />
          <span className="font-semibold text-gray-800">Active Trace</span>
        </div>
        <div className="flex items-center gap-4">
          {session && (
            <span className="text-sm text-gray-500">
              {session.user.email}
            </span>
          )}
          <button
            type="button"
            onClick={logout}
            className="text-sm text-red-600 hover:underline"
          >
            Cerrar sesión
          </button>
        </div>
      </header>

      <div className="flex flex-1">
        <nav
          aria-label="Navegación principal"
          className="w-56 bg-gray-50 border-r border-gray-200 py-4 flex flex-col gap-1"
        >
          {visibleItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end
              className={({ isActive }) =>
                `px-4 py-2 text-sm rounded mx-2 transition-colors ${
                  isActive
                    ? 'bg-blue-100 text-blue-700 font-medium'
                    : 'text-gray-700 hover:bg-gray-100'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}

          {showProfesor && (
            <div className="mt-4">
              <span className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                {PROFESOR_SECTION.label}
              </span>
              <div className="mt-1 flex flex-col gap-1">
                {visibleProfesorItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end
                    className={({ isActive }) =>
                      `px-4 py-2 text-sm rounded mx-2 transition-colors ${
                        isActive
                          ? 'bg-blue-100 text-blue-700 font-medium'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                ))}
              </div>
            </div>
          )}

          {showTutor && (
            <div className="mt-4">
              <span className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                {TUTOR_SECTION.label}
              </span>
              <div className="mt-1 flex flex-col gap-1">
                {visibleTutorItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end
                    className={({ isActive }) =>
                      `px-4 py-2 text-sm rounded mx-2 transition-colors ${
                        isActive
                          ? 'bg-blue-100 text-blue-700 font-medium'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                ))}
              </div>
            </div>
          )}

          {showAlumno && (
            <div className="mt-4">
              <span className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                {ALUMNO_SECTION.label}
              </span>
              <div className="mt-1 flex flex-col gap-1">
                {visibleAlumnoItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end
                    className={({ isActive }) =>
                      `px-4 py-2 text-sm rounded mx-2 transition-colors ${
                        isActive
                          ? 'bg-blue-100 text-blue-700 font-medium'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                ))}
              </div>
            </div>
          )}

          {showLiquidaciones && (
            <div className="mt-4">
              <span className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                {LIQUIDACIONES_SECTION.label}
              </span>
              <div className="mt-1 flex flex-col gap-1">
                {visibleLiquidacionesItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end
                    className={({ isActive }) =>
                      `px-4 py-2 text-sm rounded mx-2 transition-colors ${
                        isActive
                          ? 'bg-blue-100 text-blue-700 font-medium'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                ))}
              </div>
            </div>
          )}

          {showAdmin && (
            <div className="mt-4">
              <span className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                {ADMIN_SECTION.label}
              </span>
              <div className="mt-1 flex flex-col gap-1">
                {visibleAdminItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end
                    className={({ isActive }) =>
                      `px-4 py-2 text-sm rounded mx-2 transition-colors ${
                        isActive
                          ? 'bg-blue-100 text-blue-700 font-medium'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                ))}
              </div>
            </div>
          )}

          {showCoordinacion && (
            <div className="mt-4">
              <span className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                {COORDINACION_SECTION.label}
              </span>
              <div className="mt-1 flex flex-col gap-1">
                {visibleCoordinacionItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end
                    className={({ isActive }) =>
                      `px-4 py-2 text-sm rounded mx-2 transition-colors ${
                        isActive
                          ? 'bg-blue-100 text-blue-700 font-medium'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                ))}
              </div>
            </div>
          )}
        </nav>

        <main className="flex-1 p-6">
          <Suspense fallback={<p className="text-sm text-gray-500">Cargando…</p>}>
            <Outlet />
          </Suspense>
        </main>
      </div>
    </div>
  );
}
