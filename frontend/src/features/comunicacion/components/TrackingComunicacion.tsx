import { useLoteStatus } from '../hooks/useComunicacion';
import { Card, StatusBadge, type EstadoSemantico } from '@/shared/ui';

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

  // Estados de cola con su color semántico centralizado (spec frontend-ui-restyle).
  const celdas: { label: string; count: number; estado: EstadoSemantico }[] = [
    { label: 'Pendiente', count: data.pendientes, estado: 'pendiente-cola' },
    { label: 'En envío', count: data.enviando, estado: 'en-envio' },
    { label: 'Enviado', count: data.enviados, estado: 'enviado' },
    { label: 'Fallido', count: data.errores, estado: 'fallido' },
    { label: 'Cancelado', count: data.cancelados, estado: 'cancelado' },
  ];

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

      <div className="grid grid-cols-5 gap-3">
        {celdas.map((c) => (
          <Card key={c.label} className="flex flex-col items-center gap-1 text-center">
            <span className="text-2xl font-semibold text-gray-800">{c.count}</span>
            <StatusBadge estado={c.estado}>{c.label}</StatusBadge>
          </Card>
        ))}
      </div>

      <p className="text-xs text-gray-400">Lote ID: {loteId}</p>
    </div>
  );
}
