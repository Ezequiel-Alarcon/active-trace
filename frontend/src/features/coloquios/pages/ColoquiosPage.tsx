import { useState } from 'react';
import { PageHeader, Button, DataTable, KpiCard, StatusBadge, type Column } from '@/shared/ui';
import { useMetricasColoquios, useConvocatorias, useReservas } from '../hooks/useColoquios';
import FormConvocatoria from '../components/FormConvocatoria';
import type { ConvocatoriaResponse, ReservaResponse } from '../types/coloquios';

export default function ColoquiosPage() {
  const [showForm, setShowForm] = useState(false);
  const [convocatoriaSeleccionada, setConvocatoriaSeleccionada] = useState<string | null>(null);
  const { data: metrics, isLoading: loadMet } = useMetricasColoquios();
  const { data: convocatorias, isLoading: loadConv, isError: errConv } = useConvocatorias();
  const { data: reservas } = useReservas(convocatoriaSeleccionada ?? '');

  const convColumns: Column<ConvocatoriaResponse>[] = [
    { header: 'Materia', render: (c) => c.materia_nombre },
    { header: 'Instancia', render: (c) => c.instancia },
    { header: 'Cupos libres', render: (c) => String(c.cupos_libres) },
    { header: 'Reservas activas', render: (c) => String(c.reservas_activas) },
    { header: 'Convocados', render: (c) => String(c.convocados) },
    { header: 'Estado', render: (c) => <StatusBadge estado={c.estado === 'activa' ? 'aprobado' : 'cancelado'}>{c.estado}</StatusBadge> },
    {
      header: 'Acciones',
      render: (c) => (
        <Button variant="secondary" onClick={() => setConvocatoriaSeleccionada(c.id)}>
          Ver reservas
        </Button>
      ),
    },
  ];

  const resColumns: Column<ReservaResponse>[] = [
    { header: 'Alumno', render: (r) => r.alumno_nombre },
    { header: 'Día', render: (r) => r.dia },
    { header: 'Hora', render: (r) => r.hora },
    { header: 'Estado', render: (r) => <StatusBadge estado={r.estado === 'activa' ? 'aprobado' : 'cancelado'}>{r.estado}</StatusBadge> },
  ];

  if (showForm) {
    return (
      <div className="flex flex-col gap-4">
        <PageHeader title="Nueva convocatoria" actions={<Button variant="secondary" onClick={() => setShowForm(false)}>Cancelar</Button>} />
        <FormConvocatoria onSuccess={() => setShowForm(false)} />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Coloquios" actions={<Button onClick={() => setShowForm(true)}>Nueva convocatoria</Button>} />

      <div className="grid grid-cols-4 gap-4">
        <KpiCard label="Total alumnos" value={loadMet ? '…' : String(metrics?.total_alumnos ?? 0)} />
        <KpiCard label="Instancias activas" value={loadMet ? '…' : String(metrics?.instancias_activas ?? 0)} />
        <KpiCard label="Reservas activas" value={loadMet ? '…' : String(metrics?.reservas_activas ?? 0)} />
        <KpiCard label="Notas registradas" value={loadMet ? '…' : String(metrics?.notas_registradas ?? 0)} />
      </div>

      <h2 className="text-lg font-semibold text-gray-800 mt-2">Convocatorias</h2>
      {loadConv && <p className="text-sm text-gray-500">Cargando convocatorias…</p>}
      {errConv && <p role="alert" className="text-sm text-red-600">Error al cargar convocatorias.</p>}
      {!loadConv && !errConv && (
        <DataTable rows={convocatorias ?? []} columns={convColumns} rowKey={(c) => c.id} emptyMessage="No hay convocatorias registradas." />
      )}

      {convocatoriaSeleccionada && (
        <div className="border-t border-gray-200 pt-4 mt-4">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold text-gray-800">Reservas activas</h2>
            <Button variant="secondary" onClick={() => setConvocatoriaSeleccionada(null)}>Cerrar</Button>
          </div>
          <DataTable rows={reservas ?? []} columns={resColumns} rowKey={(r) => r.id} emptyMessage="No hay reservas activas." />
        </div>
      )}
    </div>
  );
}
