import { useMemo, useState } from 'react';
import { useMaterias } from '../hooks/useMaterias';

interface MateriaSelectorProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
  disabled?: boolean;
}

const INPUT_CLASS = 'border border-gray-300 rounded px-3 py-2 text-sm w-full';

export default function MateriaSelector({ value, onChange, error, disabled }: MateriaSelectorProps) {
  const { data: materias = [], isLoading } = useMaterias();
  const [search, setSearch] = useState('');

  const filteredMaterias = useMemo(() => {
    const normalized = search.trim().toLowerCase();
    if (!normalized) {
      return materias;
    }

    return materias.filter((materia) => {
      const target = `${materia.codigo} ${materia.nombre}`.toLowerCase();
      return target.includes(normalized);
    });
  }, [materias, search]);

  return (
    <div className="flex flex-col gap-2">
      <label htmlFor="materia_id" className="text-sm font-medium text-gray-700">
        Materia
      </label>
      <input
        id="materia_search"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        placeholder="Buscar materia por nombre o código"
        className={INPUT_CLASS}
        disabled={disabled}
      />
      <select
        id="materia_id"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className={INPUT_CLASS}
        disabled={disabled || isLoading}
      >
        <option value="">Seleccionar materia</option>
        {filteredMaterias.map((materia) => (
          <option key={materia.id} value={materia.id}>
            {materia.codigo} · {materia.nombre}
          </option>
        ))}
      </select>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
