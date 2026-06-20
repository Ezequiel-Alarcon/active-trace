import { useEffect, useMemo, useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { Button } from '@/shared/ui';
import { useCreateSlot } from '../hooks/useCreateSlot';
import { slotFormSchema, type SlotFormValues } from '../types/encuentros';
import PreviewStep from './PreviewStep';
import SlotFormStep1ContextoAcademico from './SlotFormStep1ContextoAcademico';
import SlotFormStep2DayTime from './SlotFormStep2DayTime';
import SlotFormStep3Duration from './SlotFormStep3Duration';
import {
  SLOT_WIZARD_STORAGE_KEY,
  applyValidationErrors,
  clearStoredSlotWizardState,
  getDefaultSlotFormValues,
  loadStoredSlotWizardState,
  saveStoredSlotWizardState,
  toCreateSlotRequest,
} from './encuentrosFormUtils';

interface SlotFormWizardProps {
  onSuccess?: () => void;
}

const STEP_TITLES = ['Contexto', 'Día y hora', 'Duración', 'Preview'];
const FIELDS_BY_STEP: Array<Array<keyof SlotFormValues>> = [
  ['materia_id', 'cohorte_id'],
  ['dia_semana', 'hora_inicio', 'hora_fin', 'modalidad', 'link'],
  ['fecha_inicio', 'cant_semanas', 'titulo'],
  [],
];

export default function SlotFormWizard({ onSuccess }: SlotFormWizardProps) {
  const storedState = useMemo(() => loadStoredSlotWizardState(), []);
  const [step, setStep] = useState(storedState?.step ?? 0);
  const [apiError, setApiError] = useState<string | null>(null);
  const mutation = useCreateSlot();
  const form = useForm<SlotFormValues>({
    resolver: zodResolver(slotFormSchema),
    defaultValues: storedState?.values ?? getDefaultSlotFormValues(),
  });
  const values = form.watch();

  useEffect(() => {
    saveStoredSlotWizardState({ step, values });
  }, [step, values]);

  async function goNext() {
    const isValid = await form.trigger(FIELDS_BY_STEP[step]);
    if (isValid) {
      setStep((current) => Math.min(current + 1, STEP_TITLES.length - 1));
    }
  }

  function goBack() {
    setStep((current) => Math.max(current - 1, 0));
  }

  async function onSubmit(data: SlotFormValues) {
    setApiError(null);

    try {
      await mutation.mutateAsync(toCreateSlotRequest(data));
      clearStoredSlotWizardState();
      form.reset(getDefaultSlotFormValues());
      setStep(0);
      onSuccess?.();
    } catch (error) {
      const handled = applyValidationErrors(error, form.setError, {
        meet_url: 'link',
        video_url: 'link',
      });

      if (!handled) {
        setApiError('No se pudo crear el slot. Intentá nuevamente.');
      }
    }
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-2" aria-label="Pasos del wizard">
        {STEP_TITLES.map((title, index) => (
          <div
            key={title}
            className={`rounded-full px-3 py-1 text-sm ${
              step === index ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'
            }`}
          >
            {index + 1}. {title}
          </div>
        ))}
      </div>

      {apiError && <p role="alert" className="text-sm text-red-600">{apiError}</p>}
      {mutation.isSuccess && (
        <p role="status" className="text-sm text-green-700">
          Slot creado correctamente.
        </p>
      )}

      {step === 0 && (
        <SlotFormStep1ContextoAcademico
          materiaId={values.materia_id}
          cohorteId={values.cohorte_id}
          onMateriaChange={(value) => form.setValue('materia_id', value, { shouldValidate: true })}
          onCohorteChange={(value) => form.setValue('cohorte_id', value, { shouldValidate: true })}
          materiaError={form.formState.errors.materia_id?.message}
          cohorteError={form.formState.errors.cohorte_id?.message}
          disabled={mutation.isPending}
        />
      )}

      {step === 1 && (
        <SlotFormStep2DayTime
          diaSemana={Number(values.dia_semana)}
          horaInicio={values.hora_inicio}
          horaFin={values.hora_fin}
          modalidad={values.modalidad}
          link={values.link}
          onFieldChange={(field, value) =>
            form.setValue(field as keyof SlotFormValues, value as never, { shouldValidate: true })
          }
          errors={{
            dia_semana: form.formState.errors.dia_semana?.message,
            hora_inicio: form.formState.errors.hora_inicio?.message,
            hora_fin: form.formState.errors.hora_fin?.message,
            link: form.formState.errors.link?.message,
          }}
          disabled={mutation.isPending}
        />
      )}

      {step === 2 && (
        <SlotFormStep3Duration
          fechaInicio={values.fecha_inicio}
          cantSemanas={Number(values.cant_semanas)}
          titulo={values.titulo}
          onFieldChange={(field, value) =>
            form.setValue(field as keyof SlotFormValues, value as never, { shouldValidate: true })
          }
          errors={{
            fecha_inicio: form.formState.errors.fecha_inicio?.message,
            cant_semanas: form.formState.errors.cant_semanas?.message,
            titulo: form.formState.errors.titulo?.message,
          }}
          disabled={mutation.isPending}
        />
      )}

      {step === 3 && <PreviewStep values={values} />}

      <div className="flex justify-between gap-2">
        <Button type="button" variant="secondary" onClick={goBack} disabled={step === 0 || mutation.isPending}>
          Anterior
        </Button>

        {step < STEP_TITLES.length - 1 ? (
          <Button type="button" onClick={goNext} disabled={mutation.isPending}>
            Siguiente
          </Button>
        ) : (
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Creando…' : 'Crear slot'}
          </Button>
        )}
      </div>

      <input type="hidden" value={SLOT_WIZARD_STORAGE_KEY} readOnly aria-hidden="true" />
    </form>
  );
}
