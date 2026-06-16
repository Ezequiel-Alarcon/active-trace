import { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import SeleccionDestinatarios from '../components/SeleccionDestinatarios';
import PreviewComunicacion from '../components/PreviewComunicacion';
import TrackingComunicacion from '../components/TrackingComunicacion';

interface ComisionContext {
  comisionId: string;
}

type ComunicacionStep = 'seleccion' | 'preview' | 'tracking';

/**
 * Multi-step page for sending comunicaciones to alumnos atrasados.
 * Steps: select recipients → preview → send & track.
 */
export default function ComunicarPage() {
  const ctx = useOutletContext<ComisionContext | null>();
  const comisionId = ctx?.comisionId ?? null;

  const [step, setStep] = useState<ComunicacionStep>('seleccion');
  const [selectedEmails, setSelectedEmails] = useState<string[]>([]);
  const [loteId, setLoteId] = useState<string | null>(null);

  if (!comisionId) {
    return (
      <p className="text-sm text-gray-500">
        Seleccioná una comisión para comunicar.
      </p>
    );
  }

  if (step === 'tracking' && loteId) {
    return <TrackingComunicacion loteId={loteId} />;
  }

  if (step === 'preview') {
    return (
      <PreviewComunicacion
        destinatarios={selectedEmails}
        onConfirm={(newLoteId) => {
          setLoteId(newLoteId);
          setStep('tracking');
        }}
        onBack={() => setStep('seleccion')}
      />
    );
  }

  return (
    <SeleccionDestinatarios
      comisionId={comisionId}
      onNext={(emails) => {
        setSelectedEmails(emails);
        setStep('preview');
      }}
    />
  );
}
