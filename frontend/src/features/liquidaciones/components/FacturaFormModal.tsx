import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreateFactura } from '../hooks/useFacturas';
import { Button } from '@/shared/ui';

const schema = z.object({
  docente_id: z.string().min(1, 'Docente es requerido'),
  periodo: z.string().min(1, 'Período es requerido'),
  detalle: z.string().min(1, 'Detalle es requerido'),
  archivo_url: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface FacturaFormModalProps {
  onClose: () => void;
}

export default function FacturaFormModal({ onClose }: FacturaFormModalProps) {
  const create = useCreateFactura();

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { docente_id: '', periodo: '', detalle: '', archivo_url: null },
  });

  function onSubmit(data: FormData) {
    create.mutate(data, { onSuccess: onClose });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-lg font-semibold mb-4">Registrar factura</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-3">
          <div>
            <label className="text-sm text-gray-600">Docente ID</label>
            <input {...register('docente_id')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
            {errors.docente_id && <p className="text-xs text-red-600">{errors.docente_id.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">Período</label>
            <input type="month" {...register('periodo')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
            {errors.periodo && <p className="text-xs text-red-600">{errors.periodo.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">Detalle</label>
            <textarea {...register('detalle')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" rows={3} />
            {errors.detalle && <p className="text-xs text-red-600">{errors.detalle.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">URL archivo (opcional)</label>
            <input {...register('archivo_url')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
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
