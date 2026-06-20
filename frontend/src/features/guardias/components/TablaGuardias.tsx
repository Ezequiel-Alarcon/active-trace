import { DataTable } from '@/shared/ui';
import type { Column } from '@/shared/ui';
import type { GuardiaResponse } from '../types/guardias';

interface TablaGuardiasProps {
  guardias: GuardiaResponse[];
}

const COLUMNS: Column<GuardiaResponse>[] = [
  {
    header: 'Fecha',
    render: (row) => row.fecha,
  },
  {
    header: 'Hora inicio',
    render: (row) => row.hora_inicio,
  },
  {
    header: 'Hora fin',
    render: (row) => row.hora_fin,
  },
  {
    header: 'Título',
    render: (row) => row.titulo ?? '—',
  },
  {
    header: 'Observaciones',
    render: (row) => row.observaciones ?? '—',
    className: 'max-w-xs truncate',
  },
];

export default function TablaGuardias({ guardias }: TablaGuardiasProps) {
  return (
    <DataTable
      columns={COLUMNS}
      rows={guardias}
      rowKey={(row) => row.id}
      emptyMessage="No hay guardias registradas."
    />
  );
}
