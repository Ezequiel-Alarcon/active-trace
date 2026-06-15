import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useLogin } from '../hooks/useLogin';

const loginSchema = z.object({
  tenant_codigo: z.string().min(1, 'El código de institución es obligatorio'),
  email: z.string().email('Ingresá un email válido'),
  password: z.string().min(1, 'La contraseña es obligatoria'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

const twoFaSchema = z.object({
  totp_code: z
    .string()
    .length(6, 'El código debe tener 6 dígitos')
    .regex(/^\d+$/, 'Solo dígitos'),
});

type TwoFaFormValues = z.infer<typeof twoFaSchema>;

export default function LoginForm() {
  const { step, error, isLoading, submitCredentials, submit2fa } = useLogin();

  const credentialsForm = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { tenant_codigo: '', email: '', password: '' },
  });

  const twoFaForm = useForm<TwoFaFormValues>({
    resolver: zodResolver(twoFaSchema),
    defaultValues: { totp_code: '' },
  });

  if (step === '2fa') {
    return (
      <form
        aria-label="Verificación en dos pasos"
        onSubmit={twoFaForm.handleSubmit((data) => submit2fa(data.totp_code))}
        className="flex flex-col gap-4 w-full max-w-sm"
      >
        <h2 className="text-xl font-semibold">Verificación en dos pasos</h2>
        <p className="text-sm text-gray-600">
          Ingresá el código de 6 dígitos de tu app de autenticación.
        </p>

        <div className="flex flex-col gap-1">
          <label htmlFor="totp_code" className="text-sm font-medium">
            Código TOTP
          </label>
          <input
            id="totp_code"
            type="text"
            inputMode="numeric"
            maxLength={6}
            {...twoFaForm.register('totp_code')}
            className="border rounded px-3 py-2 text-center tracking-widest"
          />
          {twoFaForm.formState.errors.totp_code && (
            <span className="text-red-600 text-xs">
              {twoFaForm.formState.errors.totp_code.message}
            </span>
          )}
        </div>

        {error && (
          <p role="alert" className="text-red-600 text-sm">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
        >
          {isLoading ? 'Verificando…' : 'Verificar'}
        </button>
      </form>
    );
  }

  return (
    <form
      aria-label="Iniciar sesión"
      onSubmit={credentialsForm.handleSubmit(submitCredentials)}
      className="flex flex-col gap-4 w-full max-w-sm"
    >
      <h2 className="text-xl font-semibold">Iniciar sesión</h2>

      <div className="flex flex-col gap-1">
        <label htmlFor="tenant_codigo" className="text-sm font-medium">
          Código de institución
        </label>
        <input
          id="tenant_codigo"
          type="text"
          {...credentialsForm.register('tenant_codigo')}
          className="border rounded px-3 py-2"
        />
        {credentialsForm.formState.errors.tenant_codigo && (
          <span className="text-red-600 text-xs">
            {credentialsForm.formState.errors.tenant_codigo.message}
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
          {...credentialsForm.register('email')}
          className="border rounded px-3 py-2"
        />
        {credentialsForm.formState.errors.email && (
          <span className="text-red-600 text-xs">
            {credentialsForm.formState.errors.email.message}
          </span>
        )}
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="password" className="text-sm font-medium">
          Contraseña
        </label>
        <input
          id="password"
          type="password"
          {...credentialsForm.register('password')}
          className="border rounded px-3 py-2"
        />
        {credentialsForm.formState.errors.password && (
          <span className="text-red-600 text-xs">
            {credentialsForm.formState.errors.password.message}
          </span>
        )}
      </div>

      {error && (
        <p role="alert" className="text-red-600 text-sm">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
      >
        {isLoading ? 'Ingresando…' : 'Ingresar'}
      </button>

      <a href="/forgot" className="text-sm text-blue-600 hover:underline text-center">
        ¿Olvidaste tu contraseña?
      </a>
    </form>
  );
}
