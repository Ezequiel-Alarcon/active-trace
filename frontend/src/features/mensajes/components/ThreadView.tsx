import { useState } from 'react';
import { Button, Card } from '@/shared/ui';
import { useThread } from '../hooks/useMensajes';
import MensajeForm from './MensajeForm';
import type { MensajeResponse } from '../types/mensajes';

interface ThreadViewProps {
  hiloId: string;
}

function MensajeBubble({ mensaje }: { mensaje: MensajeResponse }) {
  return (
    <div className="flex flex-col gap-1 p-3 rounded-lg bg-gray-50 border border-gray-100">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-gray-600">{mensaje.asunto}</span>
        <span className="text-xs text-gray-400">
          {new Date(mensaje.created_at).toLocaleString('es-AR', {
            day: '2-digit',
            month: '2-digit',
            year: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>
      <p className="text-sm text-gray-800 whitespace-pre-wrap">{mensaje.cuerpo}</p>
    </div>
  );
}

export default function ThreadView({ hiloId }: ThreadViewProps) {
  const { data, isLoading, isError } = useThread(hiloId);
  const [replyOpen, setReplyOpen] = useState(false);

  const mensajes = data ?? [];
  const lastMensaje: MensajeResponse | undefined = mensajes[mensajes.length - 1];

  if (isLoading) return <p className="text-sm text-gray-500">Cargando…</p>;
  if (isError) return <p className="text-sm text-red-500">Error al cargar los datos.</p>;

  return (
    <div className="flex flex-col gap-3 h-full">
      <div className="flex flex-col gap-2 overflow-y-auto flex-1">
        {mensajes.length === 0 && (
          <p className="text-sm text-gray-400">No hay mensajes.</p>
        )}
        {mensajes.map((m) => (
          <MensajeBubble key={m.id} mensaje={m} />
        ))}
      </div>

      {!replyOpen && lastMensaje && (
        <div className="pt-2 border-t border-gray-100">
          <Button variant="secondary" onClick={() => setReplyOpen(true)}>
            Responder
          </Button>
        </div>
      )}

      {replyOpen && lastMensaje && (
        <Card className="mt-2">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Responder</h3>
          <MensajeForm
            mode="reply"
            lastMensaje={lastMensaje}
            onSuccess={() => setReplyOpen(false)}
            onCancel={() => setReplyOpen(false)}
          />
        </Card>
      )}
    </div>
  );
}
