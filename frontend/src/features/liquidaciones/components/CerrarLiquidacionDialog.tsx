import { useState } from 'react';
import { useCerrarLiquidacion } from '../hooks/useLiquidaciones';
import { Button } from '@/shared/ui';

interface CerrarLiquidacionDialogProps {
  periodo: string;
  onClose: () => void;
}

export default function CerrarLiquidacionDialog({
  periodo,
  onClose,
}: CerrarLiquidacionDialogProps) {
  const { mutate: cerrar, isPending, isError, error } = useCerrarLiquidacion();
  const [success, setSuccess] = useState(false);

  function handleConfirm() {
    cerrar(periodo, {
      onSuccess: () => {
        setSuccess(true);
        setTimeout(onClose, 2000);
      },
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-2">
          Cerrar liquidación
        </h2>

        {success ? (
          <p className="text-green-700 text-sm">Liquidación cerrada correctamente</p>
        ) : (
          <>
            <p className="text-sm text-gray-600 mb-4">
              ¿Está seguro de cerrar la liquidación del período? Esta acción es irreversible.
            </p>

            {isError && (
              <p role="alert" className="text-sm text-red-600 mb-3">
                {error?.message ?? 'Error al cerrar la liquidación.'}
              </p>
            )}

            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={onClose} disabled={isPending}>
                Cancelar
              </Button>
              <Button variant="danger" onClick={handleConfirm} disabled={isPending}>
                {isPending ? 'Cerrando…' : 'Cerrar liquidación'}
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
