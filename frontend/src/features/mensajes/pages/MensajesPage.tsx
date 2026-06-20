import { useState } from 'react';
import { PageHeader, Button, Card } from '@/shared/ui';
import { useInbox } from '../hooks/useMensajes';
import InboxList from '../components/InboxList';
import ThreadView from '../components/ThreadView';
import MensajeForm from '../components/MensajeForm';

export default function MensajesPage() {
  const { data, isLoading, isError } = useInbox();
  const [selectedHiloId, setSelectedHiloId] = useState<string | null>(null);
  const [newMessageOpen, setNewMessageOpen] = useState(false);

  const threads = data ?? [];

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="Mensajes"
        actions={
          <Button onClick={() => { setNewMessageOpen(true); setSelectedHiloId(null); }}>
            + Nuevo mensaje
          </Button>
        }
      />

      {newMessageOpen && (
        <Card>
          <h2 className="text-lg font-medium text-gray-800 mb-4">Nuevo mensaje</h2>
          <MensajeForm
            mode="new"
            onSuccess={() => setNewMessageOpen(false)}
            onCancel={() => setNewMessageOpen(false)}
          />
        </Card>
      )}

      <div className="flex gap-4 h-[calc(100vh-12rem)]">
        <div className="w-72 flex-shrink-0 border border-gray-200 rounded-lg bg-white overflow-y-auto">
          <div className="px-4 py-3 border-b border-gray-100">
            <span className="text-sm font-semibold text-gray-700">Bandeja de entrada</span>
          </div>
          {isLoading && <p className="text-sm text-gray-500 px-4 py-3">Cargando…</p>}
          {isError && <p className="text-sm text-red-500 px-4 py-3">Error al cargar los datos.</p>}
          {!isLoading && !isError && (
            <InboxList
              threads={threads}
              selectedHiloId={selectedHiloId}
              onSelect={(hiloId) => { setSelectedHiloId(hiloId); setNewMessageOpen(false); }}
            />
          )}
        </div>

        <div className="flex-1 border border-gray-200 rounded-lg bg-white p-4 overflow-y-auto">
          {!selectedHiloId && !newMessageOpen && (
            <div className="flex items-center justify-center h-full">
              <p className="text-sm text-gray-400">Seleccioná un hilo para ver los mensajes.</p>
            </div>
          )}
          {selectedHiloId && !newMessageOpen && (
            <ThreadView hiloId={selectedHiloId} />
          )}
        </div>
      </div>
    </div>
  );
}
