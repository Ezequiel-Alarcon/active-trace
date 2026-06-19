import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreateSalarioPlus, useUpdateSalarioPlus } from '../hooks/useGrillaSalarial';
import { Button } from '@/shared/ui';
import type { SalarioPlus } from '../types/liquidaciones';

const ROLES = ['PROFESOR', 'TUTOR', 'NEXO', 'COORDINADOR'];

const schema = z.object({
  clave: z.string().min(1, 'Clave es requerida'),
  rol: z.string().min(1, 'Rol es requerido'),
  descripcion: z.string().min(1, 'Descripción es requerida'),
  importe: z.coerce.number().positive('Importe debe ser positivo'),
  vigencia_desde: z.string().min(1, 'Fecha de inicio es requerida'),
  vigencia_hasta: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface SalarioPlusFormModalProps {
  salario: SalarioPlus | null;
  onClose: () => void;
}

export default function SalarioPlusFormModal({ salario, onClose }: SalarioPlusFormModalProps) {
  const create = useCreateSalarioPlus();
  const update = useUpdateSalarioPlus();
  const isEdit = Boolean(salario);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: salario
      ? { clave: salario.clave, rol: salario.rol, descripcion: salario.descripcion, importe: salario.importe, vigencia_desde: salario.vigencia_desde, vigencia_hasta: salario.vigencia_hasta }
      : { clave: '', rol: '', descripcion: '', importe: 0, vigencia_desde: '', vigencia_hasta: null },
  });

  function onSubmit(data: FormData) {
    if (isEdit && salario) {
      update.mutate({ id: salario.id, data }, { onSuccess: onClose });
    } else {
      create.mutate(data, { onSuccess: onClose });
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-lg font-semibold mb-4">{isEdit ? 'Editar' : 'Agregar'} Salario Plus</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-3">
          <div>
            <label className="text-sm text-gray-600">Clave</label>
            <input {...register('clave')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
            {errors.clave && <p className="text-xs text-red-600">{errors.clave.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">Rol</label>
            <select {...register('rol')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full">
              <option value="">Seleccionar</option>
              {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
            {errors.rol && <p className="text-xs text-red-600">{errors.rol.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">Descripción</label>
            <textarea {...register('descripcion')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" rows={2} />
            {errors.descripcion && <p className="text-xs text-red-600">{errors.descripcion.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">Importe</label>
            <input type="number" step="0.01" {...register('importe')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
            {errors.importe && <p className="text-xs text-red-600">{errors.importe.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">Vigencia desde</label>
            <input type="date" {...register('vigencia_desde')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
            {errors.vigencia_desde && <p className="text-xs text-red-600">{errors.vigencia_desde.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">Vigencia hasta (opcional)</label>
            <input type="date" {...register('vigencia_hasta')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
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
