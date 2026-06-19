import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/shared/ui';
import { useAsignacionMasiva } from '../hooks/useEquipos';
import type { AsignacionMasivaRequest } from '../types/equipos';

const schema = z.object({
  docente_ids: z.string().min(1, 'Seleccione al menos un docente'),
  materia_id: z.string().min(1, 'Seleccione una materia'),
  carrera: z.string().min(1, 'Ingrese la carrera'),
  cohorte: z.string().min(1, 'Ingrese la cohorte'),
  rol: z.string().min(1, 'Seleccione un rol'),
  vigencia_desde: z.string().min(1, 'Ingrese fecha de inicio'),
  vigencia_hasta: z.string().min(1, 'Ingrese fecha de fin'),
});

type FormValues = z.infer<typeof schema>;

const INPUT_CLASS = 'border border-gray-300 rounded px-3 py-1.5 text-sm w-full';

export default function FormAsignacionMasiva() {
  const [step, setStep] = useState(0);
  const mutation = useAsignacionMasiva();

  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      docente_ids: '',
      materia_id: '',
      carrera: '',
      cohorte: '',
      rol: '',
      vigencia_desde: '',
      vigencia_hasta: '',
    },
  });

  function onSubmit(data: FormValues) {
    const request: AsignacionMasivaRequest = {
      ...data,
      docente_ids: data.docente_ids.split(',').map((d) => d.trim()),
    };
    mutation.mutate(request);
  }

  if (mutation.isSuccess) {
    return (
      <div role="status" className="p-4 bg-green-50 rounded border border-green-200 text-green-700 text-sm">
        Asignación masiva completada: {mutation.data.creadas} asignaciones creadas.
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4 max-w-lg">
      {mutation.isError && (
        <p role="alert" className="text-sm text-red-600">{mutation.error.message}</p>
      )}

      {step === 0 && (
        <div className="flex flex-col gap-3">
          <label className="text-sm font-medium text-gray-700">IDs de docentes (separados por coma)</label>
          <input {...register('docente_ids')} className={INPUT_CLASS} placeholder="u-1, u-2, u-3" />
          {errors.docente_ids && <span className="text-red-600 text-xs">{errors.docente_ids.message}</span>}
        </div>
      )}

      {step === 1 && (
        <div className="flex flex-col gap-3">
          <label className="text-sm font-medium text-gray-700">Materia</label>
          <input {...register('materia_id')} className={INPUT_CLASS} placeholder="m-1" />
          {errors.materia_id && <span className="text-red-600 text-xs">{errors.materia_id.message}</span>}
          <label className="text-sm font-medium text-gray-700">Carrera</label>
          <input {...register('carrera')} className={INPUT_CLASS} placeholder="Ing. en Sistemas" />
          {errors.carrera && <span className="text-red-600 text-xs">{errors.carrera.message}</span>}
          <label className="text-sm font-medium text-gray-700">Cohorte</label>
          <input {...register('cohorte')} className={INPUT_CLASS} placeholder="2025" />
          {errors.cohorte && <span className="text-red-600 text-xs">{errors.cohorte.message}</span>}
        </div>
      )}

      {step === 2 && (
        <div className="flex flex-col gap-3">
          <label className="text-sm font-medium text-gray-700">Rol</label>
          <select {...register('rol')} className={INPUT_CLASS}>
            <option value="">Seleccionar rol…</option>
            <option value="TITULAR">Titular</option>
            <option value="ADJUNTO">Adjunto</option>
            <option value="JTP">JTP</option>
            <option value="AYUDANTE">Ayudante</option>
          </select>
          {errors.rol && <span className="text-red-600 text-xs">{errors.rol.message}</span>}
        </div>
      )}

      {step === 3 && (
        <div className="flex flex-col gap-3">
          <label className="text-sm font-medium text-gray-700">Vigencia desde</label>
          <input {...register('vigencia_desde')} type="date" className={INPUT_CLASS} />
          {errors.vigencia_desde && <span className="text-red-600 text-xs">{errors.vigencia_desde.message}</span>}
          <label className="text-sm font-medium text-gray-700">Vigencia hasta</label>
          <input {...register('vigencia_hasta')} type="date" className={INPUT_CLASS} />
          {errors.vigencia_hasta && <span className="text-red-600 text-xs">{errors.vigencia_hasta.message}</span>}
        </div>
      )}

      {step === 4 && (
        <div className="flex flex-col gap-3">
          <p className="text-sm text-gray-600">Revise los datos antes de confirmar la asignación masiva.</p>
        </div>
      )}

      <div className="flex gap-2">
        {step > 0 && (
          <Button type="button" variant="secondary" onClick={() => setStep((s) => s - 1)}>
            Anterior
          </Button>
        )}
        {step < 4 ? (
          <Button type="button" onClick={() => setStep((s) => s + 1)}>
            Siguiente
          </Button>
        ) : (
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Asignando…' : 'Confirmar asignación'}
          </Button>
        )}
      </div>
    </form>
  );
}
