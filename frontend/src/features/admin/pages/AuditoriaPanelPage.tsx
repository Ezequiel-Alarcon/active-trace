import { PageHeader, DataTable, EmptyState } from '@/shared/ui';
import type { Column } from '@/shared/ui';
import { useActionsPerDay, useComunicacionStatus } from '../hooks/useAuditoria';
import type { ActionsPerDayEntry, ComunicacionStatusEntry } from '../types/auditoria';

export default function AuditoriaPanelPage() {
  const { data: actionsPerDay, isLoading: loadingActions } = useActionsPerDay();
  const { data: comStatus, isLoading: loadingCom } = useComunicacionStatus();

  const actionsColumns: Column<ActionsPerDayEntry>[] = [
    { header: 'Fecha', render: (e) => e.fecha },
    { header: 'Acciones', render: (e) => e.acciones.toLocaleString() },
  ];

  const comColumns: Column<ComunicacionStatusEntry>[] = [
    { header: 'Materia', render: (e) => e.materia },
    { header: 'Docente', render: (e) => e.docente },
    { header: 'Pendientes', render: (e) => e.pendientes },
    { header: 'Enviando', render: (e) => e.enviando },
    { header: 'OK', render: (e) => e.ok },
    { header: 'Fallidos', render: (e) => e.fallidos },
    { header: 'Cancelados', render: (e) => e.cancelados },
  ];

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Panel de auditoría" />

      <div className="grid grid-cols-2 gap-4">
        <div className="border border-gray-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Acciones (últimos 7 días)</h3>
          {loadingActions && <p className="text-sm text-gray-500">Cargando…</p>}
          {!loadingActions && (!actionsPerDay || actionsPerDay.length === 0) ? (
            <EmptyState>Sin datos de acciones.</EmptyState>
          ) : (
            <DataTable rows={actionsPerDay ?? []} columns={actionsColumns} rowKey={(e) => e.fecha} />
          )}
        </div>
        <div className="border border-gray-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Comunicaciones</h3>
          {loadingCom && <p className="text-sm text-gray-500">Cargando…</p>}
          {!loadingCom && (!comStatus || comStatus.length === 0) ? (
            <EmptyState>Sin datos de comunicaciones.</EmptyState>
          ) : (
            <DataTable rows={comStatus ?? []} columns={comColumns} rowKey={(e) => `${e.materia}-${e.docente}`} />
          )}
        </div>
      </div>
    </div>
  );
}
