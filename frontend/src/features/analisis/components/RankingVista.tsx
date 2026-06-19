import { useRanking } from '../hooks/useRanking';
import { DataTable, StatusBadge, type Column } from '@/shared/ui';

interface RankingVistaProps {
  comisionId: string;
}

/**
 * Vista de ranking de actividades aprobadas.
 * Solo muestra alumnos con al menos 1 actividad aprobada (cantidad_aprobadas > 0).
 * Ordenado por cantidad_aprobadas desc (backend must return it sorted; we display as-is).
 */
export default function RankingVista({ comisionId: _comisionId }: RankingVistaProps) {
  // TODO: (REVIEW) comisionId should map to materia_id.
  // Passing comisionId as materiaId until /api/comisiones provides the mapping.
  const { data, isLoading, isError } = useRanking(_comisionId);

  if (isLoading) return <p className="text-sm text-gray-500">Cargando ranking…</p>;
  if (isError) return <p role="alert" className="text-sm text-red-600">Error al cargar ranking.</p>;

  const rankings = (data?.rankings ?? []).filter((r) => r.cantidad_aprobadas > 0);

  const columns: Column<(typeof rankings)[number]>[] = [
    { header: '#', render: (r) => r.posicion },
    {
      header: 'Alumno',
      render: (r) => (
        <div>
          <div>{r.nombre}</div>
          <div className="text-gray-400 text-xs">{r.email}</div>
        </div>
      ),
    },
    {
      header: 'Aprobadas',
      render: (r) => <StatusBadge estado="aprobado">{r.cantidad_aprobadas}</StatusBadge>,
    },
    {
      header: 'Total',
      render: (r) => <span className="text-gray-500">{r.cantidad_totales}</span>,
      className: 'text-right',
    },
    {
      header: 'Promedio',
      render: (r) => (r.nota_promedio != null ? r.nota_promedio.toFixed(1) : '—'),
      className: 'text-right',
    },
  ];

  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-lg font-medium text-gray-800">Ranking de actividades aprobadas</h2>
      <DataTable
        rows={rankings}
        columns={columns}
        rowKey={(r) => r.usuario_id}
        emptyMessage="No hay alumnos con actividades aprobadas."
      />
    </div>
  );
}
