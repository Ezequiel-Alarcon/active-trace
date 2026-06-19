import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreateMateria, useUpdateMateria } from '../hooks/useEstructura';
import { Button } from '@/shared/ui';
import type { Materia } from '../types/estructura';

const schema = z.object({
  codigo: z.string().min(1, 'Código es requerido'),
  nombre: z.string().min(1, 'Nombre es requerido'),
});

type FormData = z.infer<typeof schema>;

interface MateriaFormModalProps {
  materia: Materia | null;
  onClose: () => void;
}

export default function MateriaFormModal({ materia, onClose }: MateriaFormModalProps) {
  const create = useCreateMateria();
  const update = useUpdateMateria();
  const isEdit = Boolean(materia);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: materia ? { codigo: materia.codigo, nombre: materia.nombre } : { codigo: '', nombre: '' },
  });

  function onSubmit(data: FormData) {
    if (isEdit && materia) {
      update.mutate({ id: materia.id, data }, { onSuccess: onClose });
    } else {
      create.mutate(data, { onSuccess: onClose });
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-lg font-semibold mb-4">{isEdit ? 'Editar' : 'Agregar'} materia</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-3">
          <div>
            <label className="text-sm text-gray-600">Código</label>
            <input {...register('codigo')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
            {errors.codigo && <p className="text-xs text-red-600">{errors.codigo.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">Nombre</label>
            <input {...register('nombre')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
            {errors.nombre && <p className="text-xs text-red-600">{errors.nombre.message}</p>}
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
