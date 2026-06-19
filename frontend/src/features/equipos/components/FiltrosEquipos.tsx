import { useForm } from 'react-hook-form';
import { Button, FilterBar } from '@/shared/ui';
import type { EquipoFilters } from '../types/equipos';

interface FiltrosEquiposProps {
  onApply: (filters: EquipoFilters) => void;
}

const INPUT_CLASS = 'border border-gray-300 rounded px-3 py-1.5 text-sm';

export default function FiltrosEquipos({ onApply }: FiltrosEquiposProps) {
  const { register, handleSubmit, reset } = useForm<EquipoFilters>();

  function onSubmit(values: EquipoFilters) {
    const filters: EquipoFilters = {};
    if (values.estado) filters.estado = values.estado;
    if (values.materia) filters.materia = values.materia;
    if (values.rol) filters.rol = values.rol;
    if (values.carrera) filters.carrera = values.carrera;
    if (values.cohorte) filters.cohorte = values.cohorte;
    onApply(filters);
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <FilterBar>
        <select {...register('estado')} className={INPUT_CLASS}>
          <option value="">Todos los estados</option>
          <option value="activo">Activo</option>
          <option value="inactivo">Inactivo</option>
          <option value="vencido">Vencido</option>
        </select>
        <input {...register('materia')} placeholder="Materia" className={INPUT_CLASS} />
        <input {...register('carrera')} placeholder="Carrera" className={INPUT_CLASS} />
        <input {...register('cohorte')} placeholder="Cohorte" className={INPUT_CLASS} />
        <Button type="submit">Filtrar</Button>
        <Button type="button" variant="secondary" onClick={() => { reset(); onApply({}); }}>
          Limpiar
        </Button>
      </FilterBar>
    </form>
  );
}
