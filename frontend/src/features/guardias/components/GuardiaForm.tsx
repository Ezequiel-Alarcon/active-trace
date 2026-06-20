import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { TextField, Button } from '@/shared/ui';
import { useCreateGuardia } from '../hooks/useGuardias';

const MATERIA_OPTIONS = [
  { value: '22222222-0003-0000-0000-000000000000', label: 'AED' },
  { value: '22222222-0004-0000-0000-000000000000', label: 'POO' },
];

const COHORTE_ID_DEFAULT = '22222222-0002-0000-0000-000000000000';

const schema = z
  .object({
    materia_id: z.string().min(1, 'Requerido'),
    cohorte_id: z.string().min(1, 'Requerido'),
    fecha: z.string().min(1, 'Requerido'),
    hora_inicio: z.string().min(1, 'Requerido'),
    hora_fin: z.string().min(1, 'Requerido'),
    titulo: z.string().optional(),
    observaciones: z.string().optional(),
  })
  .refine((val) => val.hora_fin > val.hora_inicio, {
    message: 'La hora de fin debe ser posterior a la de inicio',
    path: ['hora_fin'],
  });

type FormValues = z.infer<typeof schema>;

interface GuardiaFormProps {
  onSuccess: () => void;
  onCancel: () => void;
}

export default function GuardiaForm({ onSuccess, onCancel }: GuardiaFormProps) {
  const { mutate, isPending, isError, error } = useCreateGuardia();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      materia_id: MATERIA_OPTIONS[0].value,
      cohorte_id: COHORTE_ID_DEFAULT,
    },
  });

  function onSubmit(values: FormValues) {
    mutate(
      {
        ...values,
        titulo: values.titulo || undefined,
        observaciones: values.observaciones || undefined,
      },
      { onSuccess },
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <label htmlFor="materia_id" className="text-sm font-medium text-gray-700">
          Materia
        </label>
        <select
          id="materia_id"
          {...register('materia_id')}
          className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {MATERIA_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {errors.materia_id && (
          <span className="text-red-600 text-xs">{errors.materia_id.message}</span>
        )}
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="cohorte_id" className="text-sm font-medium text-gray-700">
          Cohorte
        </label>
        <input
          id="cohorte_id"
          {...register('cohorte_id')}
          readOnly
          className="border border-gray-200 rounded px-3 py-2 text-sm bg-gray-50 text-gray-500"
        />
        {errors.cohorte_id && (
          <span className="text-red-600 text-xs">{errors.cohorte_id.message}</span>
        )}
      </div>

      <TextField
        id="fecha"
        label="Fecha"
        type="date"
        {...register('fecha')}
        error={errors.fecha?.message}
      />

      <TextField
        id="hora_inicio"
        label="Hora inicio"
        type="time"
        {...register('hora_inicio')}
        error={errors.hora_inicio?.message}
      />

      <TextField
        id="hora_fin"
        label="Hora fin"
        type="time"
        {...register('hora_fin')}
        error={errors.hora_fin?.message}
      />

      <TextField
        id="titulo"
        label="Título (opcional)"
        {...register('titulo')}
        error={errors.titulo?.message}
      />

      <div className="flex flex-col gap-1">
        <label htmlFor="observaciones" className="text-sm font-medium text-gray-700">
          Observaciones (opcional)
        </label>
        <textarea
          id="observaciones"
          {...register('observaciones')}
          rows={3}
          className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {isError && (
        <p className="text-sm text-red-500">
          {(error as Error)?.message ?? 'Error al registrar la guardia.'}
        </p>
      )}

      <div className="flex gap-2 justify-end">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={isPending}>
          Cancelar
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Guardando…' : 'Registrar guardia'}
        </Button>
      </div>
    </form>
  );
}
