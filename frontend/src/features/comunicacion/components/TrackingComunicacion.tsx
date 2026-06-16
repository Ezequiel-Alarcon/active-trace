import { useLoteStatus } from '../hooks/useComunicacion';

interface TrackingComunicacionProps {
  loteId: string;
}

/**
 * Tracking view for a comunicacion lote.
 * Polls every 4s and stops when all messages are in terminal state.
 */
export default function TrackingComunicacion({ loteId }: TrackingComunicacionProps) {
  const { data, isLoading } = useLoteStatus(loteId);

  if (isLoading || !data) {
    return <p className="text-sm text-gray-500">Cargando estado del envío…</p>;
  }

  const terminales = data.enviados + data.errores + data.cancelados;
  const allDone = terminales >= data.total && data.total > 0;

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-medium text-gray-800">Estado del envío</h2>

      {allDone ? (
        <div role="status" className="p-4 bg-green-50 rounded border border-green-200 text-sm text-green-700">
          Envío completado — todos los mensajes alcanzaron un estado terminal.
        </div>
      ) : (
        <div role="status" className="p-4 bg-blue-50 rounded border border-blue-200 text-sm text-blue-700">
          Procesando… actualizando automáticamente.
        </div>
      )}

      <div className="grid grid-cols-5 gap-3 text-center text-sm">
        <div className="p-3 rounded border border-gray-200 bg-gray-50">
          <div className="text-2xl font-semibold text-gray-700">{data.pendientes}</div>
          <div className="text-gray-500">Pendiente</div>
        </div>
        <div className="p-3 rounded border border-yellow-200 bg-yellow-50">
          <div className="text-2xl font-semibold text-yellow-700">{data.enviando}</div>
          <div className="text-yellow-600">En envío</div>
        </div>
        <div className="p-3 rounded border border-green-200 bg-green-50">
          <div className="text-2xl font-semibold text-green-700">{data.enviados}</div>
          <div className="text-green-600">OK</div>
        </div>
        <div className="p-3 rounded border border-red-200 bg-red-50">
          <div className="text-2xl font-semibold text-red-700">{data.errores}</div>
          <div className="text-red-600">Fallido</div>
        </div>
        <div className="p-3 rounded border border-gray-200 bg-gray-100">
          <div className="text-2xl font-semibold text-gray-600">{data.cancelados}</div>
          <div className="text-gray-500">Cancelado</div>
        </div>
      </div>

      <p className="text-xs text-gray-400">Lote ID: {loteId}</p>
    </div>
  );
}
