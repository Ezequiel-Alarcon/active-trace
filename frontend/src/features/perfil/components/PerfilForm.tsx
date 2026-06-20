import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { TextField, Button } from '@/shared/ui';
import { usePerfil, useUpdatePerfil } from '../hooks/usePerfil';

const schema = z.object({
  nombre: z.string().min(1, 'Requerido'),
  apellidos: z.string().min(1, 'Requerido'),
  email: z.string().email('Email inválido'),
  dni: z.string().min(1, 'Requerido'),
  cbu: z.string().optional(),
  alias_cbu: z.string().optional(),
  banco: z.string().optional(),
  regional: z.string().optional(),
  legajo: z.string().optional(),
  legajo_profesional: z.string().optional(),
  fecha_nacimiento: z.string().optional(),
  genero: z.string().optional(),
  observaciones: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

export default function PerfilForm() {
  const { data: perfil, isLoading, isError } = usePerfil();
  const { mutate, isPending, isSuccess, isError: isMutationError } = useUpdatePerfil();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  useEffect(() => {
    if (perfil) {
      reset({
        nombre: perfil.nombre,
        apellidos: perfil.apellidos,
        email: perfil.email,
        dni: perfil.dni,
        cbu: perfil.cbu ?? '',
        alias_cbu: perfil.alias_cbu ?? '',
        banco: perfil.banco ?? '',
        regional: perfil.regional ?? '',
        legajo: perfil.legajo ?? '',
        legajo_profesional: perfil.legajo_profesional ?? '',
        fecha_nacimiento: perfil.fecha_nacimiento ?? '',
        genero: perfil.genero ?? '',
        observaciones: perfil.observaciones ?? '',
      });
    }
  }, [perfil, reset]);

  if (isLoading) return <p className="text-sm text-gray-500">Cargando…</p>;
  if (isError) return <p className="text-sm text-red-500">Error al cargar los datos.</p>;

  function onSubmit(values: FormValues) {
    const payload = Object.fromEntries(
      Object.entries(values).filter(([, v]) => v !== '' && v !== undefined),
    ) as FormValues;
    mutate(payload);
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4 max-w-2xl">
      <div className="grid grid-cols-2 gap-4">
        <TextField
          id="nombre"
          label="Nombre"
          {...register('nombre')}
          error={errors.nombre?.message}
        />
        <TextField
          id="apellidos"
          label="Apellidos"
          {...register('apellidos')}
          error={errors.apellidos?.message}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <TextField
          id="email"
          label="Email"
          type="email"
          {...register('email')}
          error={errors.email?.message}
        />
        <TextField
          id="dni"
          label="DNI"
          {...register('dni')}
          error={errors.dni?.message}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <TextField
          id="cbu"
          label="CBU"
          {...register('cbu')}
          error={errors.cbu?.message}
        />
        <TextField
          id="alias_cbu"
          label="Alias CBU"
          {...register('alias_cbu')}
          error={errors.alias_cbu?.message}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <TextField
          id="banco"
          label="Banco"
          {...register('banco')}
          error={errors.banco?.message}
        />
        <TextField
          id="regional"
          label="Regional"
          {...register('regional')}
          error={errors.regional?.message}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <TextField
          id="legajo"
          label="Legajo"
          {...register('legajo')}
          error={errors.legajo?.message}
        />
        <TextField
          id="legajo_profesional"
          label="Legajo profesional"
          {...register('legajo_profesional')}
          error={errors.legajo_profesional?.message}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <TextField
          id="fecha_nacimiento"
          label="Fecha de nacimiento"
          type="date"
          {...register('fecha_nacimiento')}
          error={errors.fecha_nacimiento?.message}
        />
        <TextField
          id="genero"
          label="Género"
          {...register('genero')}
          error={errors.genero?.message}
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="observaciones" className="text-sm font-medium text-gray-700">
          Observaciones
        </label>
        <textarea
          id="observaciones"
          {...register('observaciones')}
          rows={3}
          className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {perfil && (
        <div className="text-xs text-gray-400 flex gap-4">
          <span>Facturante: {perfil.facturante ? 'Sí' : 'No'}</span>
          <span>CUIL: {perfil.cuil}</span>
        </div>
      )}

      {isMutationError && (
        <p className="text-sm text-red-500">Error al guardar los cambios.</p>
      )}
      {isSuccess && (
        <p className="text-sm text-green-600">Perfil actualizado correctamente.</p>
      )}

      <div className="flex gap-2">
        <Button type="submit" disabled={isPending || !isDirty}>
          {isPending ? 'Guardando…' : 'Guardar cambios'}
        </Button>
      </div>
    </form>
  );
}
