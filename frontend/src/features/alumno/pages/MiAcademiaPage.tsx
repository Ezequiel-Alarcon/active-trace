import { PageHeader } from '@/shared/ui';
import { useEstadoAcademico } from '../hooks/useAlumno';
import type { CalificacionItem } from '../services/alumnoApi';

function EstadoBadge({ aprobado }: { aprobado: boolean | null }) {
  if (aprobado === null) return <span className="text-gray-400 text-xs">Sin nota</span>;
  return aprobado ? (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
      Aprobado
    </span>
  ) : (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
      Desaprobado
    </span>
  );
}

function NotaCell({ item }: { item: CalificacionItem }) {
  if (item.nota === null || item.nota === undefined) return <span className="text-gray-400">—</span>;
  return <span className="font-medium">{String(item.nota)}</span>;
}

export default function MiAcademiaPage() {
  const { data, isLoading, isError } = useEstadoAcademico();

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Mi Academia" />

      {isLoading && <p className="text-sm text-gray-500">Cargando…</p>}
      {isError && <p className="text-sm text-red-500">No se pudo cargar el estado académico.</p>}

      {data && data.calificaciones.length === 0 && (
        <p className="text-sm text-gray-500">No tenés calificaciones registradas.</p>
      )}

      {data && data.calificaciones.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Código
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Materia
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nota
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Origen
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.calificaciones.map((item) => (
                <tr key={item.materia_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.materia_codigo}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {item.materia_nombre}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <NotaCell item={item} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <EstadoBadge aprobado={item.aprobado} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.origen}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
