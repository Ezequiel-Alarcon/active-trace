import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { Button, Card, TextField } from '@/shared/ui';
import { useCreateInstanciaUnica } from '../hooks/useCreateInstanciaUnica';
import {
  instanciaUnicaFormSchema,
  type InstanciaUnicaFormValues,
} from '../types/encuentros';
import CohorteSelector from './CohorteSelector';
import MateriaSelector from './MateriaSelector';
import {
  MODALIDAD_OPTIONS,
  applyValidationErrors,
  getDefaultInstanciaUnicaFormValues,
  toCreateInstanciaUnicaRequest,
} from './encuentrosFormUtils';

interface InstanciaUnicaFormProps {
  onSuccess?: () => void;
}

const SELECT_CLASS = 'border border-gray-300 rounded px-3 py-2 text-sm w-full';

export default function InstanciaUnicaForm({ onSuccess }: InstanciaUnicaFormProps) {
  const mutation = useCreateInstanciaUnica();
  const [apiError, setApiError] = useState<string | null>(null);
  const form = useForm<InstanciaUnicaFormValues>({
    resolver: zodResolver(instanciaUnicaFormSchema),
    defaultValues: getDefaultInstanciaUnicaFormValues(),
  });
  const values = form.watch();

  async function onSubmit(data: InstanciaUnicaFormValues) {
    setApiError(null);

    try {
      await mutation.mutateAsync(toCreateInstanciaUnicaRequest(data));
      form.reset(getDefaultInstanciaUnicaFormValues());
      onSuccess?.();
    } catch (error) {
      const handled = applyValidationErrors(error, form.setError, {
        meet_url: 'link',
        video_url: 'link',
      });

      if (!handled) {
        setApiError('No se pudo crear el encuentro único. Intentá nuevamente.');
      }
    }
  }

  return (
    <Card>
      <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Crear encuentro único</h2>
          <p className="text-sm text-gray-600">Creá una instancia aislada sin generar un slot recurrente.</p>
        </div>

        {apiError && <p role="alert" className="text-sm text-red-600">{apiError}</p>}
        {mutation.isSuccess && (
          <p role="status" className="text-sm text-green-700">
            Encuentro único creado correctamente.
          </p>
        )}

        <div className="grid gap-4 md:grid-cols-2">
          <MateriaSelector
            value={values.materia_id}
            onChange={(value) => form.setValue('materia_id', value, { shouldValidate: true })}
            error={form.formState.errors.materia_id?.message}
            disabled={mutation.isPending}
          />
          <CohorteSelector
            value={values.cohorte_id}
            onChange={(value) => form.setValue('cohorte_id', value, { shouldValidate: true })}
            error={form.formState.errors.cohorte_id?.message}
            disabled={mutation.isPending}
          />
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <TextField
            id="fecha"
            label="Fecha"
            type="date"
            value={values.fecha}
            onChange={(event) => form.setValue('fecha', event.target.value, { shouldValidate: true })}
            error={form.formState.errors.fecha?.message}
            disabled={mutation.isPending}
          />
          <TextField
            id="titulo"
            label="Título"
            value={values.titulo}
            onChange={(event) => form.setValue('titulo', event.target.value, { shouldValidate: true })}
            error={form.formState.errors.titulo?.message}
            disabled={mutation.isPending}
          />
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <TextField
            id="hora_inicio"
            label="Hora de inicio"
            type="time"
            value={values.hora_inicio}
            onChange={(event) => form.setValue('hora_inicio', event.target.value, { shouldValidate: true })}
            error={form.formState.errors.hora_inicio?.message}
            disabled={mutation.isPending}
          />
          <TextField
            id="hora_fin"
            label="Hora de fin"
            type="time"
            value={values.hora_fin}
            onChange={(event) => form.setValue('hora_fin', event.target.value, { shouldValidate: true })}
            error={form.formState.errors.hora_fin?.message}
            disabled={mutation.isPending}
          />
          <div className="flex flex-col gap-1">
            <label htmlFor="modalidad_form" className="text-sm font-medium text-gray-700">
              Modalidad
            </label>
            <select
              id="modalidad_form"
              value={values.modalidad}
              onChange={(event) => form.setValue('modalidad', event.target.value as InstanciaUnicaFormValues['modalidad'], { shouldValidate: true })}
              className={SELECT_CLASS}
              disabled={mutation.isPending}
            >
              {MODALIDAD_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <TextField
          id="link_form"
          label="Enlace"
          type="url"
          value={values.link}
          onChange={(event) => form.setValue('link', event.target.value, { shouldValidate: true })}
          error={form.formState.errors.link?.message}
          disabled={mutation.isPending}
        />

        <div className="flex flex-col gap-1">
          <label htmlFor="comentario" className="text-sm font-medium text-gray-700">
            Comentario (opcional)
          </label>
          <textarea
            id="comentario"
            value={values.comentario ?? ''}
            onChange={(event) => form.setValue('comentario', event.target.value, { shouldValidate: true })}
            className="min-h-24 rounded border border-gray-300 px-3 py-2 text-sm"
            disabled={mutation.isPending}
          />
        </div>

        <div className="flex justify-end">
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Creando…' : 'Crear'}
          </Button>
        </div>
      </form>
    </Card>
  );
}
