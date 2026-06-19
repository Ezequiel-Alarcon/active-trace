import { useState } from 'react';
import { useAuditLog } from '../hooks/useAuditoria';
import { PageHeader, DataTable, Button, EmptyState } from '@/shared/ui';
import type { Column } from '@/shared/ui';
import type { AuditLogEntry } from '../types/auditoria';

export default function AuditoriaLogPage() {
  const [page, setPage] = useState(0);
  const limit = 50;

  const { data, isLoading, isFetching } = useAuditLog(limit, page * limit);
  const entries = data?.entries ?? [];

  const columns: Column<AuditLogEntry>[] = [
    { header: 'Fecha/Hora', render: (e) => new Date(e.fecha_hora).toLocaleString() },
    { header: 'Usuario', render: (e) => e.usuario },
    { header: 'Acción', render: (e) => e.accion },
    { header: 'Materia', render: (e) => e.materia },
  ];

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Log de auditoría" />

      {isLoading && <p className="text-sm text-gray-500">Cargando…</p>}
      {!isLoading && entries.length === 0 ? (
        <EmptyState>No hay entradas de log.</EmptyState>
      ) : (
        <>
          <DataTable rows={entries} columns={columns} rowKey={(e) => e.id} />
          <div className="flex justify-between items-center">
            <Button variant="secondary" disabled={page === 0} onClick={() => setPage(page - 1)}>Anterior</Button>
            <span className="text-sm text-gray-500">
              {isFetching ? 'Actualizando…' : `Página ${page + 1} (${data?.total ?? 0} total)`}
            </span>
            <Button variant="secondary" disabled={entries.length < limit} onClick={() => setPage(page + 1)}>Siguiente</Button>
          </div>
        </>
      )}
    </div>
  );
}
