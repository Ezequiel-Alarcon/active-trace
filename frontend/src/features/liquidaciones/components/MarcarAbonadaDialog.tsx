import { useState } from 'react';
import { useMarcarAbonada } from '../hooks/useFacturas';
import { Button } from '@/shared/ui';

interface MarcarAbonadaDialogProps {
  facturaId: string;
  onClose: () => void;
}

export default function MarcarAbonadaDialog({ facturaId, onClose }: MarcarAbonadaDialogProps) {
  const { mutate: marcar, isPending, isError, error } = useMarcarAbonada();
  const [success, setSuccess] = useState(false);

  function handleConfirm() {
    marcar(facturaId, {
      onSuccess: () => {
        setSuccess(true);
        setTimeout(onClose, 2000);
      },
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-lg font-semibold mb-2">Marcar factura como abonada</h2>
        {success ? (
          <p className="text-green-700 text-sm">Factura marcada como abonada</p>
        ) : (
          <>
            <p className="text-sm text-gray-600 mb-4">¿Confirmar que la factura ha sido abonada?</p>
            {isError && (
              <p role="alert" className="text-sm text-red-600 mb-3">
                {error?.message ?? 'Error al marcar factura.'}
              </p>
            )}
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={onClose} disabled={isPending}>Cancelar</Button>
              <Button onClick={handleConfirm} disabled={isPending}>
                {isPending ? 'Actualizando…' : 'Confirmar abonada'}
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
