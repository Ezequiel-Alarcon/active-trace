import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { PageHeader, Button, DataTable, FilterBar, StatusBadge, type Column } from '@/shared/ui';
import { useAvisos, useEliminarAviso } from '../hooks/useAvisos';
import FormAviso from '../components/FormAviso';
import type { AvisoResponse, AvisoFilters, Alcance, Severidad, EstadoAviso } from '../types/avisos';

const INPUT_CLASS = 'border border-gray-300 rounded px-3 py-1.5 text-sm';

function mapSeveridad(s: Severidad) {
  if (s === 'Urgente') return 'atrasado' as const;
  if (s === 'Advertencia') return 'pendiente' as const;
  return 'neutro' as const;
}

function mapEstado(e: EstadoAviso) {
  return e === 'activo' ? 'aprobado' as const : 'cancelado' as const;
}

export default function AvisosPage() {
  const [filters, setFilters] = useState<AvisoFilters>({});
  const [showForm, setShowForm] = useState(false);
  const { data, isLoading, isError } = useAvisos(filters);
  const eliminar = useEliminarAviso();

  const { register, handleSubmit, reset } = useForm<AvisoFilters>();

  const avisos = data ?? [];

  const columns: Column<AvisoResponse>[] = [
    { header: 'Título', render: (a) => a.titulo },
    {
      header: 'Alcance',
      render: (a) => <StatusBadge estado="neutro">{a.alcance}</StatusBadge>,
    },
    {
      header: 'Severidad',
      render: (a) => <StatusBadge estado={mapSeveridad(a.severidad)}>{a.severidad}</StatusBadge>,
    },
    {
      header: 'Vigencia',
      render: (a) => `${a.vigencia_desde} — ${a.vigencia_hasta}`,
    },
    {
      header: 'Estado',
      render: (a) => <StatusBadge estado={mapEstado(a.estado)}>{a.estado}</StatusBadge>,
    },
    {
      header: 'ACK',
      render: (a) => a.requiere_ack ? 'Sí' : 'No',
    },
    {
      header: 'Acciones',
      render: (a) => (
        <Button
          variant="danger"
          onClick={() => { if (confirm('¿Eliminar este aviso?')) eliminar.mutate(a.id); }}
          disabled={eliminar.isPending}
        >
          Eliminar
        </Button>
      ),
    },
  ];

  function onSubmit(values: AvisoFilters) {
    const f: AvisoFilters = {};
    if (values.alcance) f.alcance = values.alcance;
    if (values.severidad) f.severidad = values.severidad;
    if (values.estado) f.estado = values.estado;
    if (values.fecha_desde) f.fecha_desde = values.fecha_desde;
    if (values.fecha_hasta) f.fecha_hasta = values.fecha_hasta;
    setFilters(f);
  }

  if (showForm) {
    return (
      <div className="flex flex-col gap-4">
        <PageHeader title="Nuevo aviso" actions={<Button variant="secondary" onClick={() => setShowForm(false)}>Cancelar</Button>} />
        <FormAviso onSuccess={() => setShowForm(false)} />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Avisos" actions={<Button onClick={() => setShowForm(true)}>Nuevo aviso</Button>} />

      <form onSubmit={handleSubmit(onSubmit)}>
        <FilterBar>
          <select {...register('alcance')} className={INPUT_CLASS}>
            <option value="">Todos los alcances</option>
            <option value="Global">Global</option>
            <option value="PorMateria">Por Materia</option>
            <option value="PorCohorte">Por Cohorte</option>
            <option value="PorRol">Por Rol</option>
          </select>
          <select {...register('severidad')} className={INPUT_CLASS}>
            <option value="">Todas las severidades</option>
            <option value="Informativo">Informativo</option>
            <option value="Advertencia">Advertencia</option>
            <option value="Urgente">Urgente</option>
          </select>
          <select {...register('estado')} className={INPUT_CLASS}>
            <option value="">Todos los estados</option>
            <option value="activo">Activo</option>
            <option value="inactivo">Inactivo</option>
          </select>
          <input {...register('fecha_desde')} type="date" placeholder="Desde" className={INPUT_CLASS} />
          <input {...register('fecha_hasta')} type="date" placeholder="Hasta" className={INPUT_CLASS} />
          <Button type="submit">Filtrar</Button>
          <Button type="button" variant="secondary" onClick={() => { reset(); setFilters({}); }}>
            Limpiar
          </Button>
        </FilterBar>
      </form>

      {isLoading && <p className="text-sm text-gray-500">Cargando avisos…</p>}
      {isError && <p role="alert" className="text-sm text-red-600">Error al cargar avisos.</p>}
      {!isLoading && !isError && (
        <DataTable
          rows={avisos}
          columns={columns}
          rowKey={(a) => a.id}
          emptyMessage="No hay avisos registrados."
        />
      )}
    </div>
  );
}
