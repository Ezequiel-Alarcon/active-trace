import { useState } from 'react';
import { PageHeader, Button } from '@/shared/ui';
import { useMisEquipos } from '../hooks/useEquipos';
import TablaEquipos from '../components/TablaEquipos';
import FiltrosEquipos from '../components/FiltrosEquipos';
import FormAsignacionMasiva from '../components/FormAsignacionMasiva';
import FormClonarEquipo from '../components/FormClonarEquipo';
import FormVigenciaEquipo from '../components/FormVigenciaEquipo';
import type { EquipoFilters } from '../types/equipos';

type Tab = 'mis-equipos' | 'asignacion-masiva' | 'clonar' | 'vigencia';

const TABS: { id: Tab; label: string }[] = [
  { id: 'mis-equipos', label: 'Mis Equipos' },
  { id: 'asignacion-masiva', label: 'Asignación Masiva' },
  { id: 'clonar', label: 'Clonar' },
  { id: 'vigencia', label: 'Vigencia' },
];

export default function EquiposPage() {
  const [tab, setTab] = useState<Tab>('mis-equipos');
  const [filters, setFilters] = useState<EquipoFilters>({});
  const { data, isLoading, isError } = useMisEquipos(filters);

  const equipos = data ?? [];

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Equipos Docentes" />

      <div className="flex gap-1 border-b border-gray-200 mb-2">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`px-3 py-2 text-sm font-medium transition-colors ${
              tab === t.id
                ? 'text-blue-700 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'mis-equipos' && (
        <div className="flex flex-col gap-4">
          <FiltrosEquipos onApply={setFilters} />
          {isLoading && <p className="text-sm text-gray-500">Cargando equipos…</p>}
          {isError && <p role="alert" className="text-sm text-red-600">Error al cargar equipos.</p>}
          {!isLoading && !isError && <TablaEquipos equipos={equipos} />}
        </div>
      )}

      {tab === 'asignacion-masiva' && <FormAsignacionMasiva />}
      {tab === 'clonar' && <FormClonarEquipo />}
      {tab === 'vigencia' && <FormVigenciaEquipo />}
    </div>
  );
}
