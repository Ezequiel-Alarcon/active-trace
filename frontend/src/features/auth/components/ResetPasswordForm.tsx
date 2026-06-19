import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useSearchParams, Link } from 'react-router-dom';
import { useReset } from '../hooks/useReset';
import { Button, TextField } from '@/shared/ui';

const resetSchema = z.object({
  new_password: z
    .string()
    .min(8, 'La contraseña debe tener al menos 8 caracteres'),
  confirm_password: z.string(),
}).refine((data) => data.new_password === data.confirm_password, {
  message: 'Las contraseñas no coinciden',
  path: ['confirm_password'],
});

type ResetFormValues = z.infer<typeof resetSchema>;

export default function ResetPasswordForm() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const { success, isLoading, error, submit } = useReset();

  const form = useForm<ResetFormValues>({
    resolver: zodResolver(resetSchema),
    defaultValues: { new_password: '', confirm_password: '' },
  });

  if (success) {
    return (
      <div className="flex flex-col gap-4 w-full max-w-sm">
        <h2 className="text-xl font-semibold">Contraseña restablecida</h2>
        <p className="text-sm text-gray-700">
          Tu contraseña fue actualizada. Redirigiendo al inicio de sesión…
        </p>
      </div>
    );
  }

  const onSubmit = (data: ResetFormValues) => {
    submit({ token, new_password: data.new_password });
  };

  return (
    <form
      aria-label="Restablecer contraseña"
      onSubmit={form.handleSubmit(onSubmit)}
      className="flex flex-col gap-4 w-full max-w-sm"
    >
      <h2 className="text-xl font-semibold">Nueva contraseña</h2>

      <TextField
        id="new_password"
        label="Nueva contraseña"
        type="password"
        error={form.formState.errors.new_password?.message}
        {...form.register('new_password')}
      />

      <TextField
        id="confirm_password"
        label="Confirmá la contraseña"
        type="password"
        error={form.formState.errors.confirm_password?.message}
        {...form.register('confirm_password')}
      />

      {error && (
        <div role="alert" className="text-red-600 text-sm flex flex-col gap-1">
          <p>{error}</p>
          <Link to="/forgot" className="text-blue-600 hover:underline text-xs">
            Solicitar un nuevo enlace
          </Link>
        </div>
      )}

      <Button type="submit" disabled={isLoading || !token}>
        {isLoading ? 'Guardando…' : 'Guardar contraseña'}
      </Button>
    </form>
  );
}
