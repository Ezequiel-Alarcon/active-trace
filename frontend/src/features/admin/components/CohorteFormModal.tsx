import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreateCohorte, useUpdateCohorte } from '../hooks/useEstructura';
import { Button } from '@/shared/ui';
import type { Carrera, Cohorte } from '../types/estructura';

const schema = z.object({
  carrera_id: z.string().min(1, 'Carrera es requerida'),
  nombre: z.string().min(1, 'Nombre es requerido'),
  anio: z.coerce.number().int().positive('Año debe ser positivo'),
  vig_desde: z.string().min(1, 'Vigencia desde es requerida'),
  vig_hasta: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface CohorteFormModalProps {
  cohorte: Cohorte | null;
  carreras: Carrera[];
  onClose: () => void;
}

export default function CohorteFormModal({ cohorte, carreras, onClose }: CohorteFormModalProps) {
  const create = useCreateCohorte();
  const update = useUpdateCohorte();
  const isEdit = Boolean(cohorte);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: cohorte
      ? { carrera_id: cohorte.carrera_id, nombre: cohorte.nombre, anio: cohorte.anio, vig_desde: cohorte.vig_desde, vig_hasta: cohorte.vig_hasta }
      : { carrera_id: '', nombre: '', anio: new Date().getFullYear(), vig_desde: '', vig_hasta: null },
  });

  function onSubmit(data: FormData) {
    if (isEdit && cohorte) {
      update.mutate({ id: cohorte.id, data }, { onSuccess: onClose });
    } else {
      create.mutate(data, { onSuccess: onClose });
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-lg font-semibold mb-4">{isEdit ? 'Editar' : 'Agregar'} cohorte</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-3">
          <div>
            <label className="text-sm text-gray-600">Carrera</label>
            <select {...register('carrera_id')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full">
              <option value="">Seleccionar</option>
              {carreras.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
            {errors.carrera_id && <p className="text-xs text-red-600">{errors.carrera_id.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">Nombre</label>
            <input {...register('nombre')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
            {errors.nombre && <p className="text-xs text-red-600">{errors.nombre.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">Año</label>
            <input type="number" {...register('anio')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
            {errors.anio && <p className="text-xs text-red-600">{errors.anio.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">Vigencia desde</label>
            <input type="date" {...register('vig_desde')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
            {errors.vig_desde && <p className="text-xs text-red-600">{errors.vig_desde.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">Vigencia hasta (opcional)</label>
            <input type="date" {...register('vig_hasta')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
          </div>
          <div className="flex justify-end gap-2 mt-2">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>Cancelar</Button>
            <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Guardando…' : 'Guardar'}</Button>
          </div>
        </form>
      </div>
    </div>
  );
}
