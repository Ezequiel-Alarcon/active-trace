import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import ComisionSelector from '../components/ComisionSelector';
import { useComisionesDisponibles } from '../hooks/useComisionesDisponibles';
import { PageHeader } from '@/shared/ui';

const COMISION_VIEWS = [
  { label: 'Importar calificaciones', to: 'importar' },
  { label: 'Atrasados', to: 'atrasados' },
  { label: 'Ranking', to: 'ranking' },
  { label: 'Notas finales', to: 'notas-finales' },
  { label: 'Reportes', to: 'reportes' },
  { label: 'Entregas sin corregir', to: 'entregas' },
  { label: 'Comunicar', to: 'comunicar' },
];

/**
 * Workspace container for a comision.
 * Holds the selected comision in local state and passes it to child routes
 * via React Router's Outlet context so it survives tab navigation.
 */
export default function ComisionPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { data: comisiones = [], isLoading } = useComisionesDisponibles();

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Comisión" />

      {isLoading ? (
        <p className="text-sm text-gray-500">Cargando comisiones…</p>
      ) : (
        <ComisionSelector
          comisiones={comisiones}
          selected={selectedId}
          onSelect={setSelectedId}
        />
      )}

      {selectedId && (
        <>
          <nav
            aria-label="Vistas de comisión"
            className="flex gap-2 border-b border-gray-200 pb-2"
          >
            {COMISION_VIEWS.map((v) => (
              <NavLink
                key={v.to}
                to={v.to}
                className={({ isActive }) =>
                  `px-3 py-1 text-sm rounded transition-colors ${
                    isActive
                      ? 'bg-blue-100 text-blue-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`
                }
              >
                {v.label}
              </NavLink>
            ))}
          </nav>

          <div className="mt-2">
            <Outlet context={{ comisionId: selectedId }} />
          </div>
        </>
      )}
    </div>
  );
}
