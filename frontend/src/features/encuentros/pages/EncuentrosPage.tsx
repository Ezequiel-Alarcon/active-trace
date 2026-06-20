import { useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { PageHeader, Button, DataTable, FilterBar, StatusBadge, type Column } from '@/shared/ui';
import { useAuth } from '@/features/auth/components/AuthProvider';
import InstanciaUnicaForm from '../components/InstanciaUnicaForm';
import SlotFormWizard from '../components/SlotFormWizard';
import { useEncuentros, useSlots, useGuardias, downloadGuardiasExport } from '../hooks/useEncuentros';
import type { InstanciaResponse, SlotResponse, GuardiaResponse, EncuentroFilters } from '../types/encuentros';

type Tab = 'encuentros' | 'slots' | 'guardias' | 'crear-slot' | 'crear-unico';

const BASE_TABS: { id: Tab; label: string }[] = [
  { id: 'encuentros', label: 'Encuentros' },
  { id: 'slots', label: 'Slots' },
  { id: 'guardias', label: 'Guardias' },
];

const MANAGEMENT_TABS: { id: Tab; label: string }[] = [
  { id: 'crear-slot', label: 'Crear slot' },
  { id: 'crear-unico', label: 'Crear único' },
];

const INPUT_CLASS = 'border border-gray-300 rounded px-3 py-1.5 text-sm';

function mapEstado(estado: string) {
  if (estado === 'activo' || estado === 'realizado') return 'aprobado' as const;
  if (estado === 'cancelado') return 'cancelado' as const;
  return 'pendiente' as const;
}

export default function EncuentrosPage() {
  const { hasPermission } = useAuth();
  const canManageEncuentros = hasPermission('encuentros:gestionar');
  const [tab, setTab] = useState<Tab>('encuentros');
  const [filters, setFilters] = useState<EncuentroFilters>({});
  const { data: encuentros, isLoading: loadEnc, isError: errEnc } = useEncuentros(filters);
  const { data: slots, isLoading: loadSlots } = useSlots();
  const { data: guardias, isLoading: loadGuard } = useGuardias(filters);
  const { register, handleSubmit, reset } = useForm<EncuentroFilters>();

  const tabs = useMemo(
    () => (canManageEncuentros ? [...BASE_TABS, ...MANAGEMENT_TABS] : BASE_TABS),
    [canManageEncuentros],
  );

  useEffect(() => {
    if (!tabs.some((currentTab) => currentTab.id === tab)) {
      setTab('encuentros');
    }
  }, [tab, tabs]);

  function onSubmit(values: EncuentroFilters) {
    const f: EncuentroFilters = {};
    if (values.materia) f.materia = values.materia;
    if (values.docente) f.docente = values.docente;
    if (values.estado) f.estado = values.estado;
    if (values.fecha_desde) f.fecha_desde = values.fecha_desde;
    if (values.fecha_hasta) f.fecha_hasta = values.fecha_hasta;
    setFilters(f);
  }

  const encColumns: Column<InstanciaResponse>[] = [
    { header: 'Materia', render: (e) => e.materia_nombre },
    { header: 'Docente', render: (e) => e.docente_nombre },
    { header: 'Día', render: (e) => e.dia },
    { header: 'Horario', render: (e) => e.horario },
    { header: 'Enlace', render: (e) => e.enlace ? <a href={e.enlace} className="text-blue-600 underline text-xs" target="_blank">Link</a> : '—' },
    { header: 'Estado', render: (e) => <StatusBadge estado={mapEstado(e.estado)}>{e.estado}</StatusBadge> },
  ];

  const slotColumns: Column<SlotResponse>[] = [
    { header: 'Materia', render: (s) => s.materia_nombre },
    { header: 'Día', render: (s) => s.dia },
    { header: 'Horario', render: (s) => s.horario },
    { header: 'Inicio', render: (s) => s.fecha_inicio },
    { header: 'Semanas', render: (s) => String(s.cantidad_semanas) },
    { header: 'Título', render: (s) => s.titulo },
  ];

  const guardColumns: Column<GuardiaResponse>[] = [
    { header: 'Tutor', render: (g) => g.tutor_nombre },
    { header: 'Materia', render: (g) => g.materia_nombre },
    { header: 'Día', render: (g) => g.dia },
    { header: 'Horario', render: (g) => g.horario },
    { header: 'Estado', render: (g) => <StatusBadge estado={mapEstado(g.estado)}>{g.estado}</StatusBadge> },
  ];

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Encuentros" />

        <div className="flex gap-1 border-b border-gray-200 mb-2">
        {tabs.map((t) => (
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

      {tab === 'encuentros' && (
        <div className="flex flex-col gap-4">
          <form onSubmit={handleSubmit(onSubmit)}>
            <FilterBar>
              <input {...register('materia')} placeholder="Materia" className={INPUT_CLASS} />
              <input {...register('docente')} placeholder="Docente" className={INPUT_CLASS} />
              <input {...register('fecha_desde')} type="date" className={INPUT_CLASS} />
              <input {...register('fecha_hasta')} type="date" className={INPUT_CLASS} />
              <Button type="submit">Filtrar</Button>
              <Button type="button" variant="secondary" onClick={() => { reset(); setFilters({}); }}>
                Limpiar
              </Button>
            </FilterBar>
          </form>
          {loadEnc && <p className="text-sm text-gray-500">Cargando encuentros…</p>}
          {errEnc && <p role="alert" className="text-sm text-red-600">Error al cargar encuentros.</p>}
          {!loadEnc && !errEnc && (
            <DataTable rows={encuentros ?? []} columns={encColumns} rowKey={(e) => e.id} emptyMessage="No hay encuentros registrados." />
          )}
        </div>
      )}

      {tab === 'slots' && (
        <div>
          {loadSlots && <p className="text-sm text-gray-500">Cargando slots…</p>}
          {!loadSlots && (
            <DataTable rows={slots ?? []} columns={slotColumns} rowKey={(s) => s.id} emptyMessage="No hay slots configurados." />
          )}
        </div>
      )}

      {tab === 'guardias' && (
        <div className="flex flex-col gap-4">
          <div className="flex justify-end">
            <Button variant="secondary" onClick={downloadGuardiasExport}>
              Exportar guardias
            </Button>
          </div>
          <form onSubmit={handleSubmit(onSubmit)}>
            <FilterBar>
              <input {...register('fecha_desde')} type="date" placeholder="Desde" className={INPUT_CLASS} />
              <input {...register('fecha_hasta')} type="date" placeholder="Hasta" className={INPUT_CLASS} />
              <Button type="submit">Filtrar</Button>
              <Button type="button" variant="secondary" onClick={() => { reset(); setFilters({}); }}>
                Limpiar
              </Button>
            </FilterBar>
          </form>
          {loadGuard && <p className="text-sm text-gray-500">Cargando guardias…</p>}
          {!loadGuard && (
            <DataTable rows={guardias ?? []} columns={guardColumns} rowKey={(g) => g.id} emptyMessage="No hay guardias registradas." />
          )}
        </div>
      )}

      {tab === 'crear-slot' && canManageEncuentros && (
        <SlotFormWizard onSuccess={() => setTab('slots')} />
      )}

      {tab === 'crear-unico' && canManageEncuentros && (
        <InstanciaUnicaForm onSuccess={() => setTab('encuentros')} />
      )}
    </div>
  );
}
