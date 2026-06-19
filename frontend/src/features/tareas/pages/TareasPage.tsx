import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { PageHeader, Button, DataTable, FilterBar, StatusBadge, type Column } from '@/shared/ui';
import { useTareas, useCambiarEstado } from '../hooks/useTareas';
import DetalleTarea from '../components/DetalleTarea';
import type { TareaResponse, TareaFilters, TareaEstado } from '../types/tareas';

const INPUT_CLASS = 'border border-gray-300 rounded px-3 py-1.5 text-sm';

const TRANSICIONES_ESTADO: Record<TareaEstado, TareaEstado[]> = {
  Pendiente: ['En progreso', 'Cancelada'],
  'En progreso': ['Resuelta', 'Cancelada'],
  Resuelta: [],
  Cancelada: [],
};

function mapEstado(estado: TareaEstado) {
  if (estado === 'En progreso') return 'en-envio' as const;
  if (estado === 'Resuelta') return 'aprobado' as const;
  if (estado === 'Cancelada') return 'cancelado' as const;
  return 'pendiente' as const;
}

export default function TareasPage() {
  const [filters, setFilters] = useState<TareaFilters>({});
  const [detalleTarea, setDetalleTarea] = useState<TareaResponse | null>(null);
  const { data, isLoading, isError } = useTareas(filters);
  const cambiarEstado = useCambiarEstado();

  const { register, handleSubmit, reset } = useForm<TareaFilters>();

  const tareas = data ?? [];

  const columns: Column<TareaResponse>[] = [
    { header: 'Título', render: (t) => t.titulo },
    { header: 'Materia', render: (t) => t.materia_nombre ?? '—' },
    { header: 'Asignado a', render: (t) => t.docente_asignado_nombre },
    { header: 'Asignado por', render: (t) => t.docente_asignador_nombre },
    {
      header: 'Estado',
      render: (t) => (
        <StatusBadge estado={mapEstado(t.estado)}>{t.estado}</StatusBadge>
      ),
    },
    {
      header: 'Acciones',
      render: (t) => (
        <div className="flex gap-1 items-center">
          <Button variant="secondary" onClick={() => setDetalleTarea(t)}>
            Ver
          </Button>
          {TRANSICIONES_ESTADO[t.estado].length > 0 && (
            <select
              className="border border-gray-300 rounded px-2 py-1 text-xs"
              onChange={(e) => {
                if (e.target.value) {
                  cambiarEstado.mutate({ id: t.id, estado: e.target.value });
                }
              }}
              defaultValue=""
            >
              <option value="" disabled>Cambiar a…</option>
              {TRANSICIONES_ESTADO[t.estado].map((est) => (
                <option key={est} value={est}>{est}</option>
              ))}
            </select>
          )}
        </div>
      ),
    },
  ];

  function onSubmit(values: TareaFilters) {
    const f: TareaFilters = {};
    if (values.estado) f.estado = values.estado;
    if (values.materia) f.materia = values.materia;
    if (values.docente) f.docente = values.docente;
    if (values.busqueda) f.busqueda = values.busqueda;
    setFilters(f);
  }

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Tareas Internas" />

      <form onSubmit={handleSubmit(onSubmit)}>
        <FilterBar>
          <select {...register('estado')} className={INPUT_CLASS}>
            <option value="">Todos los estados</option>
            <option value="Pendiente">Pendiente</option>
            <option value="En progreso">En progreso</option>
            <option value="Resuelta">Resuelta</option>
            <option value="Cancelada">Cancelada</option>
          </select>
          <input {...register('materia')} placeholder="Materia" className={INPUT_CLASS} />
          <input {...register('docente')} placeholder="Docente" className={INPUT_CLASS} />
          <input {...register('busqueda')} placeholder="Buscar…" className={INPUT_CLASS} />
          <Button type="submit">Filtrar</Button>
          <Button type="button" variant="secondary" onClick={() => { reset(); setFilters({}); }}>
            Limpiar
          </Button>
        </FilterBar>
      </form>

      {isLoading && <p className="text-sm text-gray-500">Cargando tareas…</p>}
      {isError && <p role="alert" className="text-sm text-red-600">Error al cargar tareas.</p>}
      {!isLoading && !isError && (
        <DataTable
          rows={tareas}
          columns={columns}
          rowKey={(t) => t.id}
          emptyMessage="No hay tareas registradas."
        />
      )}

      {detalleTarea && (
        <DetalleTarea tarea={detalleTarea} onClose={() => setDetalleTarea(null)} />
      )}
    </div>
  );
}
