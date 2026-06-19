import { StatusBadge, DataTable, type Column } from '@/shared/ui';
import type { AsignacionResponse } from '../types/equipos';

function mapEstado(estado: string) {
  if (estado === 'activo') return 'aprobado' as const;
  if (estado === 'inactivo') return 'pendiente' as const;
  return 'atrasado' as const;
}

interface TablaEquiposProps {
  equipos: AsignacionResponse[];
}

export default function TablaEquipos({ equipos }: TablaEquiposProps) {
  const columns: Column<AsignacionResponse>[] = [
    { header: 'Docente', render: (e) => e.docente_nombre },
    { header: 'Rol', render: (e) => e.rol },
    { header: 'Materia', render: (e) => e.materia_nombre },
    { header: 'Carrera', render: (e) => e.carrera },
    { header: 'Cohorte', render: (e) => e.cohorte },
    {
      header: 'Vigencia',
      render: (e) => `${e.vigencia_desde} — ${e.vigencia_hasta}`,
    },
    {
      header: 'Estado',
      render: (e) => (
        <StatusBadge estado={mapEstado(e.estado)}>{e.estado}</StatusBadge>
      ),
    },
  ];

  return (
    <DataTable
      rows={equipos}
      columns={columns}
      rowKey={(e) => e.id}
      emptyMessage="No hay asignaciones docentes registradas."
    />
  );
}
