import { useNotasFinales } from '../hooks/useNotasFinales';
import { DataTable, type Column } from '@/shared/ui';

/**
 * Vista de notas finales agrupadas por materia.
 */
export default function NotasFinalesVista() {
  const { data, isLoading, isError } = useNotasFinales();

  if (isLoading) return <p className="text-sm text-gray-500">Cargando notas finales…</p>;
  if (isError) return <p role="alert" className="text-sm text-red-600">Error al cargar notas finales.</p>;

  const notas = data?.notas ?? [];

  const columns: Column<(typeof notas)[number]>[] = [
    { header: 'Materia', render: (n) => n.materia_nombre },
    { header: 'Alumnos', render: (n) => n.total_alumnos, className: 'text-right' },
    { header: 'Aprobados', render: (n) => n.aprobados, className: 'text-right' },
    {
      header: 'Tasa',
      render: (n) => `${(n.tasa_aprobacion * 100).toFixed(0)}%`,
      className: 'text-right',
    },
    {
      header: 'Promedio',
      render: (n) =>
        n.nota_promedio_global != null ? n.nota_promedio_global.toFixed(1) : '—',
      className: 'text-right',
    },
  ];

  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-lg font-medium text-gray-800">Notas finales por materia</h2>
      <DataTable
        rows={notas}
        columns={columns}
        rowKey={(n) => n.materia_id}
        emptyMessage="No hay notas finales disponibles."
      />
    </div>
  );
}
