import { useEffect } from 'react';
import { usePreviewMensaje, useEnqueueMensajes } from '../hooks/useComunicacion';
import { Button, Card } from '@/shared/ui';

interface PreviewComunicacionProps {
  destinatarios: string[];
  onConfirm: (loteId: string) => void;
  onBack: () => void;
}

const DEFAULT_ASUNTO = 'Recordatorio de actividades pendientes';
const DEFAULT_CUERPO =
  'Estimado alumno, te recordamos que tenés actividades pendientes de entrega. Por favor revisá tu estado en la plataforma.';

/**
 * Preview step: shows personalized message per recipient.
 * Does NOT send until "Confirmar" is clicked.
 */
export default function PreviewComunicacion({
  destinatarios,
  onConfirm,
  onBack,
}: PreviewComunicacionProps) {
  const previewMutation = usePreviewMensaje();
  const enqueueMutation = useEnqueueMensajes();

  // Fetch preview for the first destinatario as a sample
  useEffect(() => {
    if (destinatarios.length > 0) {
      previewMutation.mutate({
        asunto: DEFAULT_ASUNTO,
        cuerpo: DEFAULT_CUERPO,
        destinatario: destinatarios[0],
      });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [destinatarios.join(',')]);

  async function handleConfirm() {
    const mensajes = destinatarios.map((email) => ({
      asunto: DEFAULT_ASUNTO,
      cuerpo: DEFAULT_CUERPO,
      destinatario: email,
    }));
    const result = await enqueueMutation.mutateAsync(mensajes);
    const loteId = result[0]?.lote_id ?? `local-${Date.now()}`;
    onConfirm(loteId);
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-medium text-gray-800">Preview de comunicación</h2>
      <p className="text-sm text-gray-600">
        Destinatarios: <strong>{destinatarios.join(', ')}</strong>
      </p>

      {previewMutation.isPending && (
        <p className="text-sm text-gray-500">Generando preview…</p>
      )}

      {previewMutation.isSuccess && (
        <Card className="flex flex-col gap-2">
          <p className="text-sm font-medium text-gray-700">
            Asunto: {previewMutation.data.asunto}
          </p>
          <p className="text-sm text-gray-600 whitespace-pre-line">
            {previewMutation.data.cuerpo}
          </p>
          <p className="text-xs text-gray-400">
            (Personalizado para cada destinatario al confirmar)
          </p>
        </Card>
      )}

      <div className="flex gap-2">
        <Button variant="secondary" onClick={onBack}>
          Volver
        </Button>
        <Button
          disabled={destinatarios.length === 0 || enqueueMutation.isPending}
          onClick={handleConfirm}
        >
          {enqueueMutation.isPending ? 'Enviando…' : 'Confirmar envío'}
        </Button>
      </div>
    </div>
  );
}
