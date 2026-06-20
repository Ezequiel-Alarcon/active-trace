import { Link } from 'react-router-dom';
import { useAuth } from '@/features/auth/components/AuthProvider';

interface QuickLink {
  label: string;
  to: string;
  description: string;
  permission?: string;
}

const ALL_QUICK_LINKS: QuickLink[] = [
  // ALUMNO
  { label: 'Mi Academia', to: '/alumno/academia', description: 'Tus calificaciones y estado de aprobación', permission: 'academico:ver_estado_propio' },
  { label: 'Mis Reservas', to: '/alumno/reservas', description: 'Reservas activas de coloquio', permission: 'coloquios:reservar' },
  // TUTOR / PROFESOR
  { label: 'Atrasados', to: '/comision/atrasados', description: 'Alumnos con atraso detectado', permission: 'atrasados:ver' },
  { label: 'Entregas sin corregir', to: '/comision/entregas', description: 'Entregas pendientes de corrección', permission: 'entregas:ver_sin_corregir' },
  { label: 'Mis Guardias', to: '/profesor/guardias', description: 'Registrá y consultá tus guardias', permission: 'encuentros:registrar_guardia' },
  { label: 'Mensajes', to: '/profesor/mensajes', description: 'Bandeja de entrada de mensajes', permission: 'mensajes:ver' },
  // COORDINADOR / PROFESOR
  { label: 'Coloquios', to: '/coordinacion/coloquios', description: 'Gestión de convocatorias y reservas', permission: 'coloquios:ver' },
  { label: 'Equipos', to: '/coordinacion/equipos', description: 'Equipos docentes por materia', permission: 'equipos:asignar' },
  { label: 'Encuentros', to: '/coordinacion/encuentros', description: 'Cronograma de encuentros', permission: 'encuentros:gestionar' },
  { label: 'Avisos', to: '/coordinacion/avisos', description: 'Publicar y gestionar avisos', permission: 'avisos:publicar' },
  // ADMIN
  { label: 'Estructura', to: '/admin/estructura', description: 'Carreras, cohortes y materias', permission: 'estructura:gestionar' },
  { label: 'Usuarios', to: '/admin/usuarios', description: 'Gestión de usuarios y roles', permission: 'usuarios:gestionar' },
  { label: 'Auditoría', to: '/admin/auditoria', description: 'Registro de actividad del sistema', permission: 'auditoria:ver' },
  // FINANZAS
  { label: 'Liquidaciones', to: '/admin/liquidaciones/periodo', description: 'Honorarios y liquidaciones', permission: 'finanzas:operar_grilla' },
];

function RoleTag() {
  const { hasPermission } = useAuth();
  if (hasPermission('estructura:gestionar')) return <span className="text-blue-700 font-semibold">Admin</span>;
  if (hasPermission('finanzas:operar_grilla')) return <span className="text-purple-700 font-semibold">Finanzas</span>;
  if (hasPermission('equipos:asignar')) return <span className="text-green-700 font-semibold">Coordinador</span>;
  if (hasPermission('calificaciones:ver')) return <span className="text-indigo-700 font-semibold">Profesor</span>;
  if (hasPermission('atrasados:ver')) return <span className="text-yellow-700 font-semibold">Tutor</span>;
  if (hasPermission('academico:ver_estado_propio')) return <span className="text-orange-700 font-semibold">Alumno</span>;
  if (hasPermission('comunicacion:aprobar')) return <span className="text-teal-700 font-semibold">Nexo</span>;
  return null;
}

export default function DashboardPage() {
  const { hasPermission, session } = useAuth();
  const nombre = session?.user?.email ?? 'usuario';

  const links = ALL_QUICK_LINKS.filter(
    (l) => !l.permission || hasPermission(l.permission),
  );

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-800">
          Bienvenido, {nombre}
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Rol activo: <RoleTag />
        </p>
      </div>

      {links.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Accesos rápidos
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {links.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className="block p-4 bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-sm transition-all"
              >
                <p className="text-sm font-medium text-gray-900">{link.label}</p>
                <p className="text-xs text-gray-500 mt-1">{link.description}</p>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
