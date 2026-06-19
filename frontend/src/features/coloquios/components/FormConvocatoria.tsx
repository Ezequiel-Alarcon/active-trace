import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/shared/ui';
import { useCrearConvocatoria } from '../hooks/useColoquios';

const schema = z.object({
  materia_id: z.string().min(1, 'Seleccione una materia'),
  instancia: z.string().min(1, 'Ingrese la instancia'),
  dias_disponibles: z.string().min(1, 'Ingrese al menos un día'),
  cupos: z.coerce.number().min(1, 'Debe haber al menos 1 cupo'),
});

type FormValues = z.infer<typeof schema>;

const INPUT_CLASS = 'border border-gray-300 rounded px-3 py-1.5 text-sm w-full';

interface FormConvocatoriaProps {
  onSuccess?: () => void;
}

export default function FormConvocatoria({ onSuccess }: FormConvocatoriaProps) {
  const mutation = useCrearConvocatoria();
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { materia_id: '', instancia: '', dias_disponibles: '', cupos: 30 },
  });

  function onSubmit(data: FormValues) {
    mutation.mutate({
      materia_id: data.materia_id,
      instancia: data.instancia,
      dias_disponibles: data.dias_disponibles.split(',').map((d) => d.trim()),
      cupos: data.cupos,
    }, {
      onSuccess: () => onSuccess?.(),
    });
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4 max-w-lg">
      {mutation.isError && (
        <p role="alert" className="text-sm text-red-600">{mutation.error.message}</p>
      )}

      <div className="flex flex-col gap-1">
        <label htmlFor="materia_id" className="text-sm font-medium text-gray-700">ID Materia</label>
        <input id="materia_id" {...register('materia_id')} className={INPUT_CLASS} />
        {errors.materia_id && <span className="text-red-600 text-xs">{errors.materia_id.message}</span>}
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="instancia" className="text-sm font-medium text-gray-700">Instancia</label>
        <input id="instancia" {...register('instancia')} className={INPUT_CLASS} placeholder="ej: 1er Parcial" />
        {errors.instancia && <span className="text-red-600 text-xs">{errors.instancia.message}</span>}
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="dias_disponibles" className="text-sm font-medium text-gray-700">Días disponibles (separados por coma)</label>
        <input id="dias_disponibles" {...register('dias_disponibles')} className={INPUT_CLASS} placeholder="2025-03-10, 2025-03-12" />
        {errors.dias_disponibles && <span className="text-red-600 text-xs">{errors.dias_disponibles.message}</span>}
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="cupos" className="text-sm font-medium text-gray-700">Cupos por día</label>
        <input id="cupos" {...register('cupos')} type="number" className={INPUT_CLASS} />
        {errors.cupos && <span className="text-red-600 text-xs">{errors.cupos.message}</span>}
      </div>

      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? 'Creando…' : 'Crear convocatoria'}
      </Button>
    </form>
  );
}
