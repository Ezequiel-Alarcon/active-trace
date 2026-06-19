import { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { PageHeader, Button, DataTable, FilterBar, type Column } from '@/shared/ui';
import { useMonitorGeneral } from '../hooks/useMonitorGeneral';
import type { MonitorFilters, MonitorEntry } from '../types/monitor';

const INPUT_CLASS = 'border border-gray-300 rounded px-3 py-1.5 text-sm';

export default function MonitorGeneralPage() {
  const [filters, setFilters] = useState<MonitorFilters>({});
  const { data, isLoading, isError } = useMonitorGeneral(filters);
  const { register, handleSubmit, reset } = useForm<MonitorFilters>();

  const datos: MonitorEntry[] = data?.datos ?? [];

  const columns: Column<MonitorEntry>[] = [
    { header: 'Alumno', render: (d) => String(d.nombre ?? '—') },
    { header: 'Email', render: (d) => <span className="text-gray-500">{String(d.email ?? '—')}</span> },
    { header: 'Comisión', render: (d) => String(d.comision ?? '—') },
    { header: 'Regional', render: (d) => String(d.regional ?? '—') },
    { header: 'Actividad', render: (d) => String(d.actividad ?? '—') },
  ];

  function onSubmit(values: MonitorFilters) {
    const f: MonitorFilters = {};
    if (values.materia) f.materia = values.materia;
    if (values.regional) f.regional = values.regional;
    if (values.comision) f.comision = values.comision;
    if (values.busqueda) f.busqueda = values.busqueda;
    if (values.estado) f.estado = values.estado;
    setFilters(f);
  }

  const handleExport = useCallback(() => {
    const csv = [
      ['Alumno', 'Email', 'Comisión', 'Regional', 'Actividad'].join(','),
      ...datos.map((d) =>
        [d.nombre ?? '', d.email ?? '', d.comision ?? '', d.regional ?? '', d.actividad ?? ''].join(','),
      ),
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'monitor-general.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  }, [datos]);

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="Monitor General"
        actions={
          <Button variant="secondary" onClick={handleExport} disabled={datos.length === 0}>
            Exportar
          </Button>
        }
      />

      <form onSubmit={handleSubmit(onSubmit)}>
        <FilterBar>
          <input {...register('materia')} placeholder="Materia" className={INPUT_CLASS} />
          <input {...register('regional')} placeholder="Regional" className={INPUT_CLASS} />
          <input {...register('comision')} placeholder="Comisión" className={INPUT_CLASS} />
          <input {...register('busqueda')} placeholder="Buscar alumno…" className={INPUT_CLASS} />
          <input {...register('estado')} placeholder="Estado" className={INPUT_CLASS} />
          <Button type="submit">Filtrar</Button>
          <Button type="button" variant="secondary" onClick={() => { reset(); setFilters({}); }}>
            Limpiar filtros
          </Button>
        </FilterBar>
      </form>

      {isLoading && <p className="text-sm text-gray-500">Cargando monitor general…</p>}
      {isError && <p role="alert" className="text-sm text-red-600">Error al cargar el monitor general.</p>}
      {!isLoading && !isError && (
        <DataTable
          rows={datos}
          columns={columns}
          rowKey={(d, idx) => String(d.usuario_id ?? idx)}
          emptyMessage="No hay alumnos que coincidan con los filtros."
        />
      )}
    </div>
  );
}
