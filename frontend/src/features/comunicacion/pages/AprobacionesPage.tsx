import { useState } from 'react';
import { PageHeader, Button, DataTable, StatusBadge, type Column } from '@/shared/ui';
import { useLotesPendientes } from '../hooks/useComunicacion';
import DetalleLoteModal from '../components/DetalleLoteModal';
import type { LotePendienteResponse } from '../types/comunicacion';

function truncateAsunto(asunto: string, max = 50): string {
  if (asunto.length <= max) return asunto;
  return asunto.slice(0, max) + '…';
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

export default function AprobacionesPage() {
  const { data: lotes, isLoading, isError } = useLotesPendientes();
  const [detalleLote, setDetalleLote] = useState<LotePendienteResponse | null>(null);

  // Sort: most recent first (created_at descending)
  const sortedLotes = [...(lotes ?? [])].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );

  const columns: Column<LotePendienteResponse>[] = [
    {
      header: 'Fecha',
      render: (l) => formatDate(l.created_at),
    },
    {
      header: 'Destinatarios',
      render: (l) => l.total,
    },
    {
      header: 'Asunto',
      render: (l) => truncateAsunto(l.asunto),
    },
    {
      header: 'Estado',
      render: () => <StatusBadge estado="pendiente">Pendiente</StatusBadge>,
    },
    {
      header: 'Acciones',
      render: (l) => (
        <Button variant="secondary" onClick={() => setDetalleLote(l)}>
          Ver
        </Button>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Aprobaciones de Comunicaciones" />

      {isLoading && <p className="text-sm text-gray-500">Cargando lote…</p>}
      {isError && <p role="alert" className="text-sm text-red-600">Error al cargar lote.</p>}
      {!isLoading && !isError && (
        <DataTable
          rows={sortedLotes}
          columns={columns}
          rowKey={(l) => l.lote_id}
          emptyMessage="No hay comunicaciones pendientes de aprobación"
        />
      )}

      {detalleLote && (
        <DetalleLoteModal
          lote={detalleLote}
          onClose={() => setDetalleLote(null)}
        />
      )}
    </div>
  );
}
