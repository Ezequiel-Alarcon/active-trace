import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/shared/ui';
import { useClonarEquipo } from '../hooks/useEquipos';

const schema = z.object({
  origen_materia_id: z.string().min(1, 'Seleccione materia origen'),
  origen_carrera: z.string().min(1, 'Ingrese carrera origen'),
  origen_cohorte: z.string().min(1, 'Ingrese cohorte origen'),
  destino_materia_id: z.string().min(1, 'Seleccione materia destino'),
  destino_carrera: z.string().min(1, 'Ingrese carrera destino'),
  destino_cohorte: z.string().min(1, 'Ingrese cohorte destino'),
});

type FormValues = z.infer<typeof schema>;

const INPUT_CLASS = 'border border-gray-300 rounded px-3 py-1.5 text-sm w-full';

export default function FormClonarEquipo() {
  const mutation = useClonarEquipo();
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  function onSubmit(data: FormValues) {
    mutation.mutate(data);
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4 max-w-lg">
      <h3 className="text-sm font-semibold text-gray-700">Origen</h3>
      <div className="flex flex-col gap-3">
        <input {...register('origen_materia_id')} placeholder="Materia ID origen" className={INPUT_CLASS} />
        {errors.origen_materia_id && <span className="text-red-600 text-xs">{errors.origen_materia_id.message}</span>}
        <input {...register('origen_carrera')} placeholder="Carrera origen" className={INPUT_CLASS} />
        <input {...register('origen_cohorte')} placeholder="Cohorte origen" className={INPUT_CLASS} />
      </div>

      <h3 className="text-sm font-semibold text-gray-700">Destino</h3>
      <div className="flex flex-col gap-3">
        <input {...register('destino_materia_id')} placeholder="Materia ID destino" className={INPUT_CLASS} />
        {errors.destino_materia_id && <span className="text-red-600 text-xs">{errors.destino_materia_id.message}</span>}
        <input {...register('destino_carrera')} placeholder="Carrera destino" className={INPUT_CLASS} />
        <input {...register('destino_cohorte')} placeholder="Cohorte destino" className={INPUT_CLASS} />
      </div>

      {mutation.isSuccess && (
        <div role="status" className="text-sm text-green-700">
          Equipo clonado: {mutation.data.asignaciones.length} asignaciones creadas.
        </div>
      )}
      {mutation.isError && (
        <p role="alert" className="text-sm text-red-600">{mutation.error.message}</p>
      )}

      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? 'Clonando…' : 'Clonar equipo'}
      </Button>
    </form>
  );
}
