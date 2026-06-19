import { useState } from 'react';
import { useAtrasados } from '../hooks/useAtrasados';
import type { AlumnoAtrasado } from '../types/analisis';
import { Button, DataTable, StatusBadge, type Column } from '@/shared/ui';

interface TablaAtrasadosProps {
  comisionId: string;
  /** Called when the user selects recipients for communication */
  onSeleccionarDestinatarios?: (emails: string[]) => void;
}

/**
 * Table of alumnos atrasados for a comision.
 * Shows empty state when no data or no activities are configured.
 */
export default function TablaAtrasados({
  comisionId: _comisionId,
  onSeleccionarDestinatarios,
}: TablaAtrasadosProps) {
  const { data, isLoading, isError } = useAtrasados();
  const [selected, setSelected] = useState<Set<string>>(new Set());

  if (isLoading) return <p className="text-sm text-gray-500">Cargando atrasados…</p>;
  if (isError) return <p role="alert" className="text-sm text-red-600">Error al cargar atrasados.</p>;

  const alumnos: AlumnoAtrasado[] = data?.alumnos ?? [];

  function toggle(email: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(email)) next.delete(email);
      else next.add(email);
      return next;
    });
  }

  const canCommunicate = selected.size > 0;

  const columns: Column<AlumnoAtrasado>[] = [
    { header: 'Alumno', render: (a) => a.nombre },
    { header: 'Email', render: (a) => <span className="text-gray-500">{a.email}</span> },
    { header: 'Materia', render: (a) => a.materia_nombre },
    { header: 'Estado', render: (a) => <StatusBadge estado="atrasado">{a.estado}</StatusBadge> },
  ];

  return (
    <div className="flex flex-col gap-3">
      {alumnos.length > 0 && (
        <div className="flex justify-between items-center">
          <p className="text-sm text-gray-600">
            {alumnos.length} alumno{alumnos.length !== 1 ? 's' : ''} atrasado
            {alumnos.length !== 1 ? 's' : ''}
          </p>
          {onSeleccionarDestinatarios && (
            <Button
              disabled={!canCommunicate}
              onClick={() => onSeleccionarDestinatarios(Array.from(selected))}
            >
              Comunicar seleccionados ({selected.size})
            </Button>
          )}
        </div>
      )}
      <DataTable
        rows={alumnos}
        columns={columns}
        rowKey={(a) => a.email}
        emptyMessage="No hay alumnos atrasados para esta comisión o aún no se importaron datos."
        selection={
          onSeleccionarDestinatarios
            ? {
                selectedKeys: selected,
                onToggle: toggle,
                ariaLabel: (a) => `Seleccionar ${a.nombre}`,
              }
            : undefined
        }
      />
    </div>
  );
}
