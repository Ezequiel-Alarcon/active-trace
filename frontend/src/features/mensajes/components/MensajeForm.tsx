import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { TextField, Button } from '@/shared/ui';
import { useSendMensaje, useReplyMensaje } from '../hooks/useMensajes';
import type { MensajeResponse } from '../types/mensajes';

const newMessageSchema = z.object({
  destinatario_id: z.string().min(1, 'Requerido'),
  asunto: z.string().min(1, 'Requerido'),
  cuerpo: z.string().min(1, 'Requerido'),
});

const replySchema = z.object({
  asunto: z.string().min(1, 'Requerido'),
  cuerpo: z.string().min(1, 'Requerido'),
});

type NewMessageValues = z.infer<typeof newMessageSchema>;
type ReplyValues = z.infer<typeof replySchema>;

interface MensajeFormNewProps {
  mode: 'new';
  onSuccess: () => void;
  onCancel: () => void;
}

interface MensajeFormReplyProps {
  mode: 'reply';
  lastMensaje: MensajeResponse;
  onSuccess: () => void;
  onCancel: () => void;
}

type MensajeFormProps = MensajeFormNewProps | MensajeFormReplyProps;

function NewMessageForm({ onSuccess, onCancel }: { onSuccess: () => void; onCancel: () => void }) {
  const { mutate, isPending, isError } = useSendMensaje();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<NewMessageValues>({ resolver: zodResolver(newMessageSchema) });

  function onSubmit(values: NewMessageValues) {
    mutate(values, { onSuccess });
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-3">
      <TextField
        id="destinatario_id"
        label="ID del destinatario"
        {...register('destinatario_id')}
        error={errors.destinatario_id?.message}
        placeholder="UUID del destinatario"
      />
      <TextField
        id="asunto"
        label="Asunto"
        {...register('asunto')}
        error={errors.asunto?.message}
      />
      <div className="flex flex-col gap-1">
        <label htmlFor="cuerpo" className="text-sm font-medium text-gray-700">
          Mensaje
        </label>
        <textarea
          id="cuerpo"
          {...register('cuerpo')}
          rows={4}
          className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {errors.cuerpo && <span className="text-red-600 text-xs">{errors.cuerpo.message}</span>}
      </div>
      {isError && <p className="text-sm text-red-500">Error al enviar el mensaje.</p>}
      <div className="flex gap-2 justify-end">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={isPending}>
          Cancelar
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Enviando…' : 'Enviar'}
        </Button>
      </div>
    </form>
  );
}

function ReplyForm({
  lastMensaje,
  onSuccess,
  onCancel,
}: {
  lastMensaje: MensajeResponse;
  onSuccess: () => void;
  onCancel: () => void;
}) {
  const { mutate, isPending, isError } = useReplyMensaje();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ReplyValues>({
    resolver: zodResolver(replySchema),
    defaultValues: { asunto: `Re: ${lastMensaje.asunto}` },
  });

  function onSubmit(values: ReplyValues) {
    mutate({ mensajeId: lastMensaje.id, data: values }, { onSuccess });
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-3">
      <TextField
        id="asunto-reply"
        label="Asunto"
        {...register('asunto')}
        error={errors.asunto?.message}
      />
      <div className="flex flex-col gap-1">
        <label htmlFor="cuerpo-reply" className="text-sm font-medium text-gray-700">
          Respuesta
        </label>
        <textarea
          id="cuerpo-reply"
          {...register('cuerpo')}
          rows={4}
          className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {errors.cuerpo && <span className="text-red-600 text-xs">{errors.cuerpo.message}</span>}
      </div>
      {isError && <p className="text-sm text-red-500">Error al enviar la respuesta.</p>}
      <div className="flex gap-2 justify-end">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={isPending}>
          Cancelar
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Enviando…' : 'Responder'}
        </Button>
      </div>
    </form>
  );
}

export default function MensajeForm(props: MensajeFormProps) {
  if (props.mode === 'new') {
    return <NewMessageForm onSuccess={props.onSuccess} onCancel={props.onCancel} />;
  }
  return (
    <ReplyForm
      lastMensaje={props.lastMensaje}
      onSuccess={props.onSuccess}
      onCancel={props.onCancel}
    />
  );
}
