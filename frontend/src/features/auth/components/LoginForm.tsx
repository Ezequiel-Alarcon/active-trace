import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button, TextField } from '@/shared/ui';
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

        <TextField
          id="totp_code"
          label="Código TOTP"
          type="text"
          inputMode="numeric"
          maxLength={6}
          className="text-center tracking-widest"
          error={twoFaForm.formState.errors.totp_code?.message}
          {...twoFaForm.register('totp_code')}
        />

        {error && (
          <p role="alert" className="text-red-600 text-sm">
            {error}
          </p>
        )}

        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Verificando…' : 'Verificar'}
        </Button>
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

      <TextField
        id="tenant_codigo"
        label="Código de institución"
        type="text"
        error={credentialsForm.formState.errors.tenant_codigo?.message}
        {...credentialsForm.register('tenant_codigo')}
      />

      <TextField
        id="email"
        label="Email"
        type="email"
        error={credentialsForm.formState.errors.email?.message}
        {...credentialsForm.register('email')}
      />

      <TextField
        id="password"
        label="Contraseña"
        type="password"
        error={credentialsForm.formState.errors.password?.message}
        {...credentialsForm.register('password')}
      />

      {error && (
        <p role="alert" className="text-red-600 text-sm">
          {error}
        </p>
      )}

      <Button type="submit" disabled={isLoading}>
        {isLoading ? 'Ingresando…' : 'Ingresar'}
      </Button>

      <a href="/forgot" className="text-sm text-blue-600 hover:underline text-center">
        ¿Olvidaste tu contraseña?
      </a>
    </form>
  );
}
