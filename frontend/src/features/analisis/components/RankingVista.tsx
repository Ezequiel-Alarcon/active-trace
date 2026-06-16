import { useRanking } from '../hooks/useRanking';

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

  if (rankings.length === 0) {
    return (
      <div role="status" className="p-4 bg-gray-50 rounded border border-gray-200 text-sm text-gray-500">
        No hay alumnos con actividades aprobadas.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-lg font-medium text-gray-800">Ranking de actividades aprobadas</h2>
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="py-2 text-left font-medium text-gray-700">#</th>
            <th className="py-2 text-left font-medium text-gray-700">Alumno</th>
            <th className="py-2 text-right font-medium text-gray-700">Aprobadas</th>
            <th className="py-2 text-right font-medium text-gray-700">Total</th>
            <th className="py-2 text-right font-medium text-gray-700">Promedio</th>
          </tr>
        </thead>
        <tbody>
          {rankings.map((r) => (
            <tr key={r.usuario_id} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="py-2">{r.posicion}</td>
              <td className="py-2">
                <div>{r.nombre}</div>
                <div className="text-gray-400 text-xs">{r.email}</div>
              </td>
              <td className="py-2 text-right font-medium">{r.cantidad_aprobadas}</td>
              <td className="py-2 text-right text-gray-500">{r.cantidad_totales}</td>
              <td className="py-2 text-right text-gray-500">
                {r.nota_promedio != null ? r.nota_promedio.toFixed(1) : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
