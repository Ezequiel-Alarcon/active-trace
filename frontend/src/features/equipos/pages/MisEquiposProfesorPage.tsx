import { PageHeader, DataTable } from '@/shared/ui';
import type { Column } from '@/shared/ui';
import { useMisEquipos } from '../hooks/useEquipos';
import type { AsignacionResponse } from '../types/equipos';

const COLUMNS: Column<AsignacionResponse>[] = [
  {
    header: 'Contexto',
    render: (row) => row.materia_nombre,
  },
  {
    header: 'Carrera',
    render: (row) => row.carrera,
  },
  {
    header: 'Cohorte',
    render: (row) => row.cohorte,
  },
  {
    header: 'Rol',
    render: (row) => row.rol,
  },
  {
    header: 'Desde',
    render: (row) => row.vigencia_desde,
  },
  {
    header: 'Hasta',
    render: (row) => row.vigencia_hasta || '—',
  },
  {
    header: 'Estado',
    render: (row) => (
      <span
        className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${
          row.estado === 'activo'
            ? 'bg-green-100 text-green-700'
            : row.estado === 'vencido'
            ? 'bg-red-100 text-red-700'
            : 'bg-gray-100 text-gray-600'
        }`}
      >
        {row.estado}
      </span>
    ),
  },
];

export default function MisEquiposProfesorPage() {
  const { data, isLoading, isError } = useMisEquipos();

  const equipos = data ?? [];

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Mis Equipos" />

      {isLoading && <p className="text-sm text-gray-500">Cargando…</p>}
      {isError && <p className="text-sm text-red-500">Error al cargar los datos.</p>}
      {!isLoading && !isError && (
        <DataTable
          columns={COLUMNS}
          rows={equipos}
          rowKey={(row) => row.id}
          emptyMessage="No hay registros."
        />
      )}
    </div>
  );
}
