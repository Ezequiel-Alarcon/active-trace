import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/shared/ui';
import { useVigenciaEquipo } from '../hooks/useEquipos';

const schema = z.object({
  equipo_id: z.string().min(1, 'Seleccione un equipo'),
  vigencia_desde: z.string().min(1, 'Ingrese fecha de inicio'),
  vigencia_hasta: z.string().min(1, 'Ingrese fecha de fin'),
});

type FormValues = z.infer<typeof schema>;

const INPUT_CLASS = 'border border-gray-300 rounded px-3 py-1.5 text-sm w-full';

export default function FormVigenciaEquipo() {
  const mutation = useVigenciaEquipo();
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  function onSubmit(data: FormValues) {
    mutation.mutate(data);
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4 max-w-lg">
      <div className="flex flex-col gap-3">
        <label className="text-sm font-medium text-gray-700">ID del equipo</label>
        <input {...register('equipo_id')} className={INPUT_CLASS} placeholder="e-1" />
        {errors.equipo_id && <span className="text-red-600 text-xs">{errors.equipo_id.message}</span>}

        <label className="text-sm font-medium text-gray-700">Vigencia desde</label>
        <input {...register('vigencia_desde')} type="date" className={INPUT_CLASS} />
        {errors.vigencia_desde && <span className="text-red-600 text-xs">{errors.vigencia_desde.message}</span>}

        <label className="text-sm font-medium text-gray-700">Vigencia hasta</label>
        <input {...register('vigencia_hasta')} type="date" className={INPUT_CLASS} />
        {errors.vigencia_hasta && <span className="text-red-600 text-xs">{errors.vigencia_hasta.message}</span>}
      </div>

      {mutation.isSuccess && (
        <div role="status" className="text-sm text-green-700">
          Vigencia actualizada: {mutation.data.actualizadas} asignaciones modificadas.
        </div>
      )}
      {mutation.isError && (
        <p role="alert" className="text-sm text-red-600">{mutation.error.message}</p>
      )}

      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? 'Actualizando…' : 'Actualizar vigencia'}
      </Button>
    </form>
  );
}
