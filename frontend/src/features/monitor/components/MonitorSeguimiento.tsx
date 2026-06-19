import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMonitorSeguimiento } from '../hooks/useMonitorSeguimiento';
import type { MonitorFilters, MonitorEntry } from '../types/monitor';
import { Button, DataTable, FilterBar, type Column } from '@/shared/ui';

const filterSchema = z.object({
  alumno: z.string().optional(),
  correo: z.string().optional(),
  comision: z.string().optional(),
  regional: z.string().optional(),
  actividad: z.string().optional(),
  minimo_cumplido: z.coerce.number().min(0).max(100).optional().nullable(),
  fecha_desde: z.string().optional(),
  fecha_hasta: z.string().optional(),
});

type FilterFormValues = z.infer<typeof filterSchema>;

const EMPTY_FILTERS: FilterFormValues = {
  alumno: '',
  correo: '',
  comision: '',
  regional: '',
  actividad: '',
  minimo_cumplido: null,
  fecha_desde: '',
  fecha_hasta: '',
};

const INPUT_CLASS = 'border border-gray-300 rounded px-3 py-1.5 text-sm';

/**
 * Monitor de seguimiento de alumnos asignados.
 * Includes filter form with Zod schema + clear action.
 */
export default function MonitorSeguimiento() {
  const [activeFilters, setActiveFilters] = useState<MonitorFilters>({});
  const { data, isLoading, isError } = useMonitorSeguimiento(activeFilters);

  const { register, handleSubmit, reset } = useForm<FilterFormValues>({
    resolver: zodResolver(filterSchema),
    defaultValues: EMPTY_FILTERS,
  });

  function onSubmit(values: FilterFormValues) {
    const filters: MonitorFilters = {};
    if (values.alumno) filters.alumno = values.alumno;
    if (values.correo) filters.correo = values.correo;
    if (values.comision) filters.comision = values.comision;
    if (values.regional) filters.regional = values.regional;
    if (values.actividad) filters.actividad = values.actividad;
    if (values.minimo_cumplido != null) filters.minimo_cumplido = values.minimo_cumplido;
    if (values.fecha_desde) filters.fecha_desde = values.fecha_desde;
    if (values.fecha_hasta) filters.fecha_hasta = values.fecha_hasta;
    setActiveFilters(filters);
  }

  function handleClear() {
    reset(EMPTY_FILTERS);
    setActiveFilters({});
  }

  const datos: MonitorEntry[] = data?.datos ?? [];

  const columns: Column<MonitorEntry>[] = [
    { header: 'Alumno', render: (d) => String(d.nombre ?? '—') },
    { header: 'Email', render: (d) => <span className="text-gray-500">{String(d.email ?? '—')}</span> },
    { header: 'Comisión', render: (d) => String(d.comision ?? '—') },
  ];

  return (
    <div className="flex flex-col gap-6">
      {/* Filter form */}
      <form onSubmit={handleSubmit(onSubmit)}>
        <FilterBar>
          <input {...register('alumno')} placeholder="Alumno" className={INPUT_CLASS} />
          <input {...register('correo')} placeholder="Correo" className={INPUT_CLASS} />
          <input {...register('comision')} placeholder="Comisión" className={INPUT_CLASS} />
          <input {...register('regional')} placeholder="Regional" className={INPUT_CLASS} />
          <input {...register('actividad')} placeholder="Actividad" className={INPUT_CLASS} />
          <input
            {...register('minimo_cumplido')}
            type="number"
            placeholder="Mínimo cumplido (%)"
            className={INPUT_CLASS}
          />
          <input
            {...register('fecha_desde')}
            type="date"
            placeholder="Desde"
            className={INPUT_CLASS}
          />
          <input
            {...register('fecha_hasta')}
            type="date"
            placeholder="Hasta"
            className={INPUT_CLASS}
          />
          <Button type="submit">Filtrar</Button>
          <Button type="button" variant="secondary" onClick={handleClear}>
            Limpiar filtros
          </Button>
        </FilterBar>
      </form>

      {/* Results */}
      {isLoading && <p className="text-sm text-gray-500">Cargando monitor…</p>}
      {isError && <p role="alert" className="text-sm text-red-600">Error al cargar el monitor.</p>}

      {!isLoading && !isError && (
        <DataTable
          rows={datos}
          columns={columns}
          rowKey={(d, idx) => String(d.usuario_id ?? idx)}
          emptyMessage="No hay alumnos que coincidan con los filtros aplicados."
        />
      )}
    </div>
  );
}
