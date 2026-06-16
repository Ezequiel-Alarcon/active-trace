import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMonitorSeguimiento } from '../hooks/useMonitorSeguimiento';
import type { MonitorFilters, MonitorEntry } from '../types/monitor';

const filterSchema = z.object({
  alumno: z.string().optional(),
  correo: z.string().optional(),
  comision: z.string().optional(),
  regional: z.string().optional(),
  actividad: z.string().optional(),
  minimo_cumplido: z.coerce.number().min(0).max(100).optional().nullable(),
});

type FilterFormValues = z.infer<typeof filterSchema>;

const EMPTY_FILTERS: FilterFormValues = {
  alumno: '',
  correo: '',
  comision: '',
  regional: '',
  actividad: '',
  minimo_cumplido: null,
};

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
    setActiveFilters(filters);
  }

  function handleClear() {
    reset(EMPTY_FILTERS);
    setActiveFilters({});
  }

  const datos: MonitorEntry[] = data?.datos ?? [];

  return (
    <div className="flex flex-col gap-6">
      {/* Filter form */}
      <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-3 gap-3">
        <input
          {...register('alumno')}
          placeholder="Alumno"
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
        />
        <input
          {...register('correo')}
          placeholder="Correo"
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
        />
        <input
          {...register('comision')}
          placeholder="Comisión"
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
        />
        <input
          {...register('regional')}
          placeholder="Regional"
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
        />
        <input
          {...register('actividad')}
          placeholder="Actividad"
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
        />
        <input
          {...register('minimo_cumplido')}
          type="number"
          placeholder="Mínimo cumplido (%)"
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
        />
        <div className="col-span-3 flex gap-2">
          <button
            type="submit"
            className="px-4 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Filtrar
          </button>
          <button
            type="button"
            onClick={handleClear}
            className="px-4 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50"
          >
            Limpiar filtros
          </button>
        </div>
      </form>

      {/* Results */}
      {isLoading && <p className="text-sm text-gray-500">Cargando monitor…</p>}
      {isError && <p role="alert" className="text-sm text-red-600">Error al cargar el monitor.</p>}

      {!isLoading && !isError && datos.length === 0 && (
        <div role="status" className="p-4 bg-gray-50 rounded border border-gray-200 text-sm text-gray-500">
          No hay alumnos que coincidan con los filtros aplicados.
        </div>
      )}

      {datos.length > 0 && (
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="py-2 text-left font-medium text-gray-700">Alumno</th>
              <th className="py-2 text-left font-medium text-gray-700">Email</th>
              <th className="py-2 text-left font-medium text-gray-700">Comisión</th>
            </tr>
          </thead>
          <tbody>
            {datos.map((d, idx) => (
              <tr key={String(d.usuario_id ?? idx)} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-2">{String(d.nombre ?? '—')}</td>
                <td className="py-2 text-gray-500">{String(d.email ?? '—')}</td>
                <td className="py-2">{String(d.comision ?? '—')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
