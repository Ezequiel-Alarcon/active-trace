import { useState } from 'react';
import { Button } from '@/shared/ui';
import { useAprobarLote } from '../hooks/useAprobarLote';
import { useRechazarLote } from '../hooks/useRechazarLote';
import type { LotePendienteResponse } from '../types/comunicacion';

interface DetalleLoteModalProps {
  lote: LotePendienteResponse;
  onClose: () => void;
}

type ConfirmAccion = 'aprobar' | 'rechazar' | null;

const MAX_CUERPO_LENGTH = 500;

function truncateCuerpo(cuerpo: string): { visible: string; truncado: boolean } {
  if (cuerpo.length <= MAX_CUERPO_LENGTH) {
    return { visible: cuerpo, truncado: false };
  }
  return { visible: cuerpo.slice(0, MAX_CUERPO_LENGTH), truncado: true };
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function DetalleLoteModal({ lote, onClose }: DetalleLoteModalProps) {
  const aprobar = useAprobarLote();
  const rechazar = useRechazarLote();
  const [confirmAccion, setConfirmAccion] = useState<ConfirmAccion>(null);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  const { visible: cuerpoVisible, truncado } = truncateCuerpo(lote.cuerpo);

  const destinatariosPreview = lote.destinatarios.slice(0, 20);
  const destinatariosExtra = lote.destinatarios.length - 20;

  function handleConfirmAprobar() {
    setConfirmAccion('aprobar');
  }

  function handleConfirmRechazar() {
    setConfirmAccion('rechazar');
  }

  async function executeConfirm() {
    if (confirmAccion === 'aprobar') {
      try {
        await aprobar.mutateAsync(lote.lote_id);
        setToastMsg('Lote aprobado correctamente');
        setTimeout(() => onClose(), 1500);
      } catch {
        setToastMsg('Error al aprobar el lote');
        setTimeout(() => setToastMsg(null), 3000);
      }
    } else if (confirmAccion === 'rechazar') {
      try {
        await rechazar.mutateAsync(lote.lote_id);
        setToastMsg('Lote rechazado');
        setTimeout(() => onClose(), 1500);
      } catch {
        setToastMsg('Error al rechazar el lote');
        setTimeout(() => setToastMsg(null), 3000);
      }
    }
    setConfirmAccion(null);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
        {confirmAccion ? (
          <div className="flex flex-col gap-4">
            <p className="text-sm text-gray-700">
              {confirmAccion === 'aprobar'
                ? `¿Aprobar este envío? Se procederá a enviar ${lote.total} mensajes.`
                : `¿Rechazar este envío? Esta acción cancelará ${lote.total} mensajes.`}
            </p>
            <div className="flex justify-end gap-2">
              <Button
                variant="secondary"
                onClick={() => setConfirmAccion(null)}
                disabled={aprobar.isPending || rechazar.isPending}
              >
                Cancelar
              </Button>
              <Button
                variant={confirmAccion === 'aprobar' ? 'primary' : 'danger'}
                onClick={executeConfirm}
                disabled={aprobar.isPending || rechazar.isPending}
              >
                Confirmar
              </Button>
            </div>
          </div>
        ) : toastMsg ? (
          <div className="flex flex-col gap-4">
            <p className="text-sm text-gray-700">{toastMsg}</p>
          </div>
        ) : (
          <>
            <h2 className="text-lg font-semibold mb-4 text-gray-800">Detalle del lote</h2>
            <div className="flex flex-col gap-3 text-sm">
              <div>
                <span className="font-medium text-gray-600">Asunto:</span>
                <p className="text-gray-900">{lote.asunto}</p>
              </div>
              <div>
                <span className="font-medium text-gray-600">Solicitado por:</span>
                <p className="text-gray-900">{lote.solicitado_por_nombre}</p>
              </div>
              <div>
                <span className="font-medium text-gray-600">Fecha:</span>
                <p className="text-gray-900">{formatDate(lote.created_at)}</p>
              </div>
              <div>
                <span className="font-medium text-gray-600">Destinatarios:</span>
                <p className="text-gray-900">{lote.total} mensaje{lote.total !== 1 ? 's' : ''}</p>
                <ul className="mt-1 flex flex-col gap-0.5 max-h-32 overflow-y-auto">
                  {destinatariosPreview.map((d, i) => (
                    <li key={i} className="text-gray-700 truncate">{d}</li>
                  ))}
                  {destinatariosExtra > 0 && (
                    <li className="text-gray-500 italic">
                      … y {destinatariosExtra} más
                    </li>
                  )}
                </ul>
              </div>
              <div>
                <span className="font-medium text-gray-600">Mensaje:</span>
                <p className="text-gray-900 whitespace-pre-wrap">{cuerpoVisible}</p>
                {truncado && <p className="text-gray-500 italic">…</p>}
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <Button variant="secondary" onClick={onClose}>
                Cerrar
              </Button>
              <Button
                variant="danger"
                onClick={handleConfirmRechazar}
                disabled={rechazar.isPending}
              >
                {rechazar.isPending ? 'Rechazando…' : 'Rechazar'}
              </Button>
              <Button
                variant="primary"
                onClick={handleConfirmAprobar}
                disabled={aprobar.isPending}
              >
                {aprobar.isPending ? 'Aprobando…' : 'Aprobar'}
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
