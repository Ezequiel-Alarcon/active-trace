import { Outlet, NavLink } from 'react-router-dom';
import { useAuth } from '@/features/auth/components/AuthProvider';
import { useLogout } from '@/features/auth/hooks/useLogout';

interface NavItem {
  label: string;
  to: string;
  permission?: string; // undefined = visible to all authenticated users
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Inicio', to: '/' }, // no permission required — visible to all authenticated users
  // C-22 entries — conditioned by permission (fail-closed via hasPermission)
  { label: 'Comisión', to: '/comision', permission: 'analisis:ver' },
  { label: 'Monitor', to: '/monitor', permission: 'analisis:ver' },
  { label: 'Comunicaciones', to: '/comision/comunicar', permission: 'comunicacion:enviar' },
];

export default function AppLayout() {
  const { hasPermission, session } = useAuth();
  const logout = useLogout();

  const visibleItems = NAV_ITEMS.filter(
    (item) => !item.permission || hasPermission(item.permission),
  );

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
        </nav>

        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
