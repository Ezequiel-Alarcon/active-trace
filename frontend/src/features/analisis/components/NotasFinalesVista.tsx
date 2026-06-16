import { useNotasFinales } from '../hooks/useNotasFinales';

/**
 * Vista de notas finales agrupadas por materia.
 */
export default function NotasFinalesVista() {
  const { data, isLoading, isError } = useNotasFinales();

  if (isLoading) return <p className="text-sm text-gray-500">Cargando notas finales…</p>;
  if (isError) return <p role="alert" className="text-sm text-red-600">Error al cargar notas finales.</p>;

  const notas = data?.notas ?? [];

  if (notas.length === 0) {
    return (
      <div role="status" className="p-4 bg-gray-50 rounded border border-gray-200 text-sm text-gray-500">
        No hay notas finales disponibles.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-lg font-medium text-gray-800">Notas finales por materia</h2>
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="py-2 text-left font-medium text-gray-700">Materia</th>
            <th className="py-2 text-right font-medium text-gray-700">Alumnos</th>
            <th className="py-2 text-right font-medium text-gray-700">Aprobados</th>
            <th className="py-2 text-right font-medium text-gray-700">Tasa</th>
            <th className="py-2 text-right font-medium text-gray-700">Promedio</th>
          </tr>
        </thead>
        <tbody>
          {notas.map((n) => (
            <tr key={n.materia_id} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="py-2">{n.materia_nombre}</td>
              <td className="py-2 text-right">{n.total_alumnos}</td>
              <td className="py-2 text-right">{n.aprobados}</td>
              <td className="py-2 text-right">{(n.tasa_aprobacion * 100).toFixed(0)}%</td>
              <td className="py-2 text-right">
                {n.nota_promedio_global != null ? n.nota_promedio_global.toFixed(1) : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
