import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useForgot } from '../hooks/useForgot';
import { Link } from 'react-router-dom';
import { Button, TextField } from '@/shared/ui';

const forgotSchema = z.object({
  tenant_codigo: z.string().min(1, 'El código de institución es obligatorio'),
  email: z.string().email('Ingresá un email válido'),
});

type ForgotFormValues = z.infer<typeof forgotSchema>;

export default function ForgotPasswordForm() {
  const { submitted, isLoading, submit } = useForgot();

  const form = useForm<ForgotFormValues>({
    resolver: zodResolver(forgotSchema),
    defaultValues: { tenant_codigo: '', email: '' },
  });

  if (submitted) {
    return (
      <div className="flex flex-col gap-4 w-full max-w-sm">
        <h2 className="text-xl font-semibold">Revisá tu email</h2>
        <p className="text-sm text-gray-700">
          Si el email está registrado, te enviamos instrucciones para restablecer tu contraseña.
        </p>
        <Link to="/login" className="text-sm text-blue-600 hover:underline">
          Volver al inicio de sesión
        </Link>
      </div>
    );
  }

  return (
    <form
      aria-label="Recuperar contraseña"
      onSubmit={form.handleSubmit(submit)}
      className="flex flex-col gap-4 w-full max-w-sm"
    >
      <h2 className="text-xl font-semibold">Recuperar contraseña</h2>

      <TextField
        id="tenant_codigo"
        label="Código de institución"
        type="text"
        error={form.formState.errors.tenant_codigo?.message}
        {...form.register('tenant_codigo')}
      />

      <TextField
        id="email"
        label="Email"
        type="email"
        error={form.formState.errors.email?.message}
        {...form.register('email')}
      />

      <Button type="submit" disabled={isLoading}>
        {isLoading ? 'Enviando…' : 'Enviar instrucciones'}
      </Button>

      <Link to="/login" className="text-sm text-blue-600 hover:underline text-center">
        Volver al inicio de sesión
      </Link>
    </form>
  );
}
