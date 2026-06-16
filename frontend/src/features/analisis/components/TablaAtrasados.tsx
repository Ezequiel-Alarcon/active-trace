import { useState } from 'react';
import { useAtrasados } from '../hooks/useAtrasados';
import type { AlumnoAtrasado } from '../types/analisis';

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

  if (alumnos.length === 0) {
    return (
      <div role="status" className="p-4 bg-gray-50 rounded border border-gray-200 text-sm text-gray-500">
        No hay alumnos atrasados para esta comisión o aún no se importaron datos.
      </div>
    );
  }

  function toggle(email: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(email)) next.delete(email);
      else next.add(email);
      return next;
    });
  }

  const canCommunicate = selected.size > 0;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex justify-between items-center">
        <p className="text-sm text-gray-600">
          {alumnos.length} alumno{alumnos.length !== 1 ? 's' : ''} atrasado{alumnos.length !== 1 ? 's' : ''}
        </p>
        {onSeleccionarDestinatarios && (
          <button
            type="button"
            disabled={!canCommunicate}
            onClick={() => onSeleccionarDestinatarios(Array.from(selected))}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            Comunicar seleccionados ({selected.size})
          </button>
        )}
      </div>
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-gray-200">
            {onSeleccionarDestinatarios && <th className="py-2 pr-3 text-left w-8"></th>}
            <th className="py-2 text-left font-medium text-gray-700">Alumno</th>
            <th className="py-2 text-left font-medium text-gray-700">Email</th>
            <th className="py-2 text-left font-medium text-gray-700">Materia</th>
            <th className="py-2 text-left font-medium text-gray-700">Estado</th>
          </tr>
        </thead>
        <tbody>
          {alumnos.map((a) => (
            <tr key={a.usuario_id} className="border-b border-gray-100 hover:bg-gray-50">
              {onSeleccionarDestinatarios && (
                <td className="py-2 pr-3">
                  <input
                    type="checkbox"
                    aria-label={`Seleccionar ${a.nombre}`}
                    checked={selected.has(a.email)}
                    onChange={() => toggle(a.email)}
                  />
                </td>
              )}
              <td className="py-2">{a.nombre}</td>
              <td className="py-2 text-gray-500">{a.email}</td>
              <td className="py-2">{a.materia_nombre}</td>
              <td className="py-2">
                <span className="px-2 py-0.5 rounded text-xs bg-red-100 text-red-700">
                  {a.estado}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
