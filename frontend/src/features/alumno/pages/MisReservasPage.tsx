import { PageHeader } from '@/shared/ui';
import { useMisReservas, useCancelarReserva } from '../hooks/useMisReservas';

function EstadoBadge({ estado }: { estado: string }) {
  const color =
    estado === 'Confirmada'
      ? 'bg-green-100 text-green-800'
      : estado === 'Cancelada'
        ? 'bg-red-100 text-red-800'
        : 'bg-yellow-100 text-yellow-800';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {estado}
    </span>
  );
}

export default function MisReservasPage() {
  const { data, isLoading, isError } = useMisReservas();
  const cancelar = useCancelarReserva();

  const reservas = data ?? [];

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Mis Reservas de Coloquio" />

      {isLoading && <p className="text-sm text-gray-500">Cargando…</p>}
      {isError && <p className="text-sm text-red-500">No se pudieron cargar las reservas.</p>}

      {!isLoading && !isError && reservas.length === 0 && (
        <p className="text-sm text-gray-500">No tenés reservas de coloquio.</p>
      )}

      {reservas.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Materia
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Instancia
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fecha reservada
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reservas.map((r) => (
                <tr key={r.reserva_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {r.materia ?? '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {r.instancia}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {r.fecha_reserva}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <EstadoBadge estado={r.estado} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    {r.estado !== 'Cancelada' && (
                      <button
                        type="button"
                        onClick={() => cancelar.mutate(r.reserva_id)}
                        disabled={cancelar.isPending}
                        className="text-sm text-red-600 hover:underline disabled:opacity-50"
                      >
                        Cancelar
                      </button>
                    )}
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
