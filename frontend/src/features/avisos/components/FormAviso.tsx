import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/shared/ui';
import { useCrearAviso, useEditarAviso } from '../hooks/useAvisos';
import type { AvisoResponse, AvisoCreate, Alcance, Severidad } from '../types/avisos';

const schema = z.object({
  titulo: z.string().min(1, 'El título es obligatorio'),
  cuerpo: z.string().min(1, 'El cuerpo es obligatorio'),
  alcance: z.enum(['Global', 'PorMateria', 'PorCohorte', 'PorRol']),
  contexto_id: z.string().optional(),
  severidad: z.enum(['Informativo', 'Advertencia', 'Urgente']),
  vigencia_desde: z.string().min(1, 'Ingrese fecha de inicio'),
  vigencia_hasta: z.string().min(1, 'Ingrese fecha de fin'),
  requiere_ack: z.boolean().optional(),
});

type FormValues = z.infer<typeof schema>;

const INPUT_CLASS = 'border border-gray-300 rounded px-3 py-1.5 text-sm w-full';
const INPUT_CLASS_TEXTAREA = 'border border-gray-300 rounded px-3 py-1.5 text-sm w-full min-h-[100px]';

interface FormAvisoProps {
  aviso?: AvisoResponse;
  onSuccess?: () => void;
}

export default function FormAviso({ aviso, onSuccess }: FormAvisoProps) {
  const crear = useCrearAviso();
  const editar = useEditarAviso();
  const isEditing = Boolean(aviso);

  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: aviso ? {
      titulo: aviso.titulo,
      cuerpo: aviso.cuerpo,
      alcance: aviso.alcance,
      contexto_id: aviso.contexto_id ?? '',
      severidad: aviso.severidad,
      vigencia_desde: aviso.vigencia_desde,
      vigencia_hasta: aviso.vigencia_hasta,
      requiere_ack: aviso.requiere_ack,
    } : {
      titulo: '',
      cuerpo: '',
      alcance: 'Global' as Alcance,
      contexto_id: '',
      severidad: 'Informativo' as Severidad,
      vigencia_desde: '',
      vigencia_hasta: '',
      requiere_ack: false,
    },
  });

  const alcanceActual = watch('alcance');
  const mutation = isEditing ? editar : crear;

  function onSubmit(data: FormValues) {
    const payload: AvisoCreate = {
      titulo: data.titulo,
      cuerpo: data.cuerpo,
      alcance: data.alcance,
      contexto_id: data.contexto_id || undefined,
      roles_destinatarios: [],
      severidad: data.severidad,
      vigencia_desde: data.vigencia_desde,
      vigencia_hasta: data.vigencia_hasta,
      requiere_ack: data.requiere_ack ?? false,
    };

    if (isEditing) {
      editar.mutateAsync({ id: aviso!.id, data: payload }).then(() => onSuccess?.());
    } else {
      crear.mutateAsync(payload).then(() => onSuccess?.());
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4 max-w-xl">
      {mutation.isError && (
        <p role="alert" className="text-sm text-red-600">{mutation.error.message}</p>
      )}

      <div className="flex flex-col gap-1">
        <label htmlFor="titulo" className="text-sm font-medium text-gray-700">Título</label>
        <input id="titulo" {...register('titulo')} className={INPUT_CLASS} />
        {errors.titulo && <span className="text-red-600 text-xs">{errors.titulo.message}</span>}
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="cuerpo" className="text-sm font-medium text-gray-700">Cuerpo</label>
        <textarea id="cuerpo" {...register('cuerpo')} className={INPUT_CLASS_TEXTAREA} />
        {errors.cuerpo && <span className="text-red-600 text-xs">{errors.cuerpo.message}</span>}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1">
          <label htmlFor="alcance" className="text-sm font-medium text-gray-700">Alcance</label>
          <select id="alcance" {...register('alcance')} className={INPUT_CLASS}>
            <option value="Global">Global</option>
            <option value="PorMateria">Por Materia</option>
            <option value="PorCohorte">Por Cohorte</option>
            <option value="PorRol">Por Rol</option>
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="severidad" className="text-sm font-medium text-gray-700">Severidad</label>
          <select id="severidad" {...register('severidad')} className={INPUT_CLASS}>
            <option value="Informativo">Informativo</option>
            <option value="Advertencia">Advertencia</option>
            <option value="Urgente">Urgente</option>
          </select>
        </div>
      </div>

      {alcanceActual !== 'Global' && (
        <div className="flex flex-col gap-1">
          <label htmlFor="contexto_id" className="text-sm font-medium text-gray-700">
            Contexto ({alcanceActual === 'PorMateria' ? 'ID Materia' : alcanceActual === 'PorCohorte' ? 'ID Cohorte' : 'Rol'})
          </label>
          <input id="contexto_id" {...register('contexto_id')} className={INPUT_CLASS} />
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1">
          <label htmlFor="vigencia_desde" className="text-sm font-medium text-gray-700">Vigencia desde</label>
          <input id="vigencia_desde" {...register('vigencia_desde')} type="date" className={INPUT_CLASS} />
          {errors.vigencia_desde && <span className="text-red-600 text-xs">{errors.vigencia_desde.message}</span>}
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="vigencia_hasta" className="text-sm font-medium text-gray-700">Vigencia hasta</label>
          <input id="vigencia_hasta" {...register('vigencia_hasta')} type="date" className={INPUT_CLASS} />
          {errors.vigencia_hasta && <span className="text-red-600 text-xs">{errors.vigencia_hasta.message}</span>}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <input id="requiere_ack" {...register('requiere_ack')} type="checkbox" className="rounded" />
        <label htmlFor="requiere_ack" className="text-sm text-gray-700">Requiere confirmación de lectura</label>
      </div>

      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? 'Guardando…' : isEditing ? 'Actualizar aviso' : 'Publicar aviso'}
      </Button>
    </form>
  );
}
