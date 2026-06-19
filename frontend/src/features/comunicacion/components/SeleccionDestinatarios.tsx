import { useState } from 'react';
import { Button } from '@/shared/ui';

interface SeleccionDestinatariosProps {
  comisionId: string;
  onNext: (emails: string[]) => void;
}

/**
 * Step 1 of comunicacion flow: select recipients from atrasados list.
 * Delegates to TablaAtrasados with selection enabled.
 *
 * NOTE: Reuses the emails collected by the caller (ComunicarPage wraps TablaAtrasados).
 * This component provides a simple email list for cases where emails are passed directly.
 */
export default function SeleccionDestinatarios({
  comisionId: _comisionId,
  onNext,
}: SeleccionDestinatariosProps) {
  const [emails, setEmails] = useState<string[]>([]);

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-gray-600">
        Seleccioná los alumnos atrasados a quienes comunicar desde la tabla de Atrasados.
        Luego presioná "Continuar".
      </p>
      <div className="flex gap-2">
        <Button disabled={emails.length === 0} onClick={() => onNext(emails)}>
          Continuar ({emails.length} destinatario{emails.length !== 1 ? 's' : ''})
        </Button>
      </div>
      {/* Placeholder: in practice the parent page (ComunicarPage) passes selected emails from TablaAtrasados */}
      <p className="text-xs text-gray-400">
        Para comunicar, usá la acción "Comunicar seleccionados" en la pestaña Atrasados.
      </p>
    </div>
  );
}
