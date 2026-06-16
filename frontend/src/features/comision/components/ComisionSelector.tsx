import type { Comision } from '../types/comision';

interface ComisionSelectorProps {
  comisiones: Comision[];
  selected: string | null;
  onSelect: (id: string) => void;
}

/**
 * Dropdown selector for materia/cohorte.
 * Shows a guide state when no selection has been made.
 */
export default function ComisionSelector({
  comisiones,
  selected,
  onSelect,
}: ComisionSelectorProps) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor="comision-select" className="text-sm font-medium text-gray-700">
        Seleccioná materia y cohorte
      </label>
      <select
        id="comision-select"
        value={selected ?? ''}
        onChange={(e) => onSelect(e.target.value)}
        className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="" disabled>
          — Seleccioná una comisión —
        </option>
        {comisiones.map((c) => (
          <option key={c.id} value={c.id}>
            {c.materia_nombre} · {c.cohorte_nombre}
          </option>
        ))}
      </select>

      {!selected && (
        <p role="status" className="text-sm text-gray-500 mt-1">
          Seleccioná una materia y cohorte para ver el análisis.
        </p>
      )}
    </div>
  );
}
