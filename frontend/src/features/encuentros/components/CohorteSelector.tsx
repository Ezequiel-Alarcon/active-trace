import { useMemo } from 'react';
import { useCohortes } from '../hooks/useCohortes';

interface CohorteSelectorProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
  disabled?: boolean;
}

const INPUT_CLASS = 'border border-gray-300 rounded px-3 py-2 text-sm w-full';

export default function CohorteSelector({ value, onChange, error, disabled }: CohorteSelectorProps) {
  const { data: cohortes = [], isLoading } = useCohortes();

  const sortedCohortes = useMemo(
    () => [...cohortes].sort((a, b) => b.anio - a.anio || a.nombre.localeCompare(b.nombre)),
    [cohortes],
  );

  return (
    <div className="flex flex-col gap-2">
      <label htmlFor="cohorte_id" className="text-sm font-medium text-gray-700">
        Cohorte
      </label>
      <select
        id="cohorte_id"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className={INPUT_CLASS}
        disabled={disabled || isLoading}
      >
        <option value="">Seleccionar cohorte</option>
        {sortedCohortes.map((cohorte) => (
          <option key={cohorte.id} value={cohorte.id}>
            {cohorte.nombre} · {cohorte.anio}
          </option>
        ))}
      </select>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
