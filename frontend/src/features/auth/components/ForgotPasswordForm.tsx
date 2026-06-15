import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useForgot } from '../hooks/useForgot';
import { Link } from 'react-router-dom';

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

      <div className="flex flex-col gap-1">
        <label htmlFor="tenant_codigo" className="text-sm font-medium">
          Código de institución
        </label>
        <input
          id="tenant_codigo"
          type="text"
          {...form.register('tenant_codigo')}
          className="border rounded px-3 py-2"
        />
        {form.formState.errors.tenant_codigo && (
          <span className="text-red-600 text-xs">
            {form.formState.errors.tenant_codigo.message}
          </span>
        )}
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="email" className="text-sm font-medium">
          Email
        </label>
        <input
          id="email"
          type="email"
          {...form.register('email')}
          className="border rounded px-3 py-2"
        />
        {form.formState.errors.email && (
          <span className="text-red-600 text-xs">
            {form.formState.errors.email.message}
          </span>
        )}
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
      >
        {isLoading ? 'Enviando…' : 'Enviar instrucciones'}
      </button>

      <Link to="/login" className="text-sm text-blue-600 hover:underline text-center">
        Volver al inicio de sesión
      </Link>
    </form>
  );
}
