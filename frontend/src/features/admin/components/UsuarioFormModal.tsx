import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreateUsuario, useUpdateUsuario } from '../hooks/useUsuarios';
import { Button } from '@/shared/ui';
import type { UsuarioTenant } from '../types/usuarios';

const ROLES = ['ADMIN', 'COORDINADOR', 'NEXO', 'FINANZAS', 'PROFESOR', 'TUTOR'] as const;

const schema = z.object({
  nombre: z.string().min(1, 'Nombre es requerido'),
  apellidos: z.string().min(1, 'Apellidos son requeridos'),
  email: z.string().email('Email inválido'),
  dni: z.string().min(1, 'DNI es requerido'),
  cuil: z.string().min(1, 'CUIL es requerido'),
  roles: z.array(z.string()).min(1, 'Al menos un rol es requerido'),
});

type FormData = z.infer<typeof schema>;

interface UsuarioFormModalProps {
  usuario: UsuarioTenant | null;
  onClose: () => void;
}

export default function UsuarioFormModal({ usuario, onClose }: UsuarioFormModalProps) {
  const create = useCreateUsuario();
  const update = useUpdateUsuario();
  const isEdit = Boolean(usuario);

  const { register, handleSubmit, formState: { errors, isSubmitting }, watch, setValue } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: usuario
      ? { nombre: usuario.nombre, apellidos: usuario.apellidos, email: usuario.email, dni: usuario.dni, cuil: usuario.cuil, roles: [...usuario.roles] }
      : { nombre: '', apellidos: '', email: '', dni: '', cuil: '', roles: [] },
  });

  const selectedRoles = watch('roles');

  function toggleRole(role: string) {
    if (selectedRoles.includes(role)) {
      setValue('roles', selectedRoles.filter((r) => r !== role), { shouldValidate: true });
    } else {
      setValue('roles', [...selectedRoles, role], { shouldValidate: true });
    }
  }

  function onSubmit(data: FormData) {
    if (isEdit && usuario) {
      update.mutate({ id: usuario.id, data }, { onSuccess: onClose });
    } else {
      create.mutate(data, { onSuccess: onClose });
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-lg font-semibold mb-4">{isEdit ? 'Editar' : 'Agregar'} usuario</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-3">
          <div>
            <label className="text-sm text-gray-600">Nombre</label>
            <input {...register('nombre')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
            {errors.nombre && <p className="text-xs text-red-600">{errors.nombre.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">Apellidos</label>
            <input {...register('apellidos')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
            {errors.apellidos && <p className="text-xs text-red-600">{errors.apellidos.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">Email</label>
            <input {...register('email')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
            {errors.email && <p className="text-xs text-red-600">{errors.email.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">DNI</label>
            {/* C-07: Usuario.dni/cuil se cifra en backend con AES-256 (UsuarioService).
                El campo llega/torna texto plano en el formulario — el cifrado es transparente al frontend. */}
            <input {...register('dni')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
            {errors.dni && <p className="text-xs text-red-600">{errors.dni.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">CUIL</label>
            {/* C-07: Usuario.dni/cuil se cifra en backend con AES-256 (UsuarioService).
                El campo llega/torna texto plano en el formulario — el cifrado es transparente al frontend. */}
            <input {...register('cuil')} className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full" />
            {errors.cuil && <p className="text-xs text-red-600">{errors.cuil.message}</p>}
          </div>
          <div>
            <label className="text-sm text-gray-600">Roles</label>
            <div className="flex flex-wrap gap-2 mt-1">
              {ROLES.map((r) => (
                <button key={r} type="button" className={`px-3 py-1 text-xs rounded-full border ${selectedRoles?.includes(r) ? 'bg-blue-100 border-blue-300 text-blue-700' : 'border-gray-200 text-gray-600 hover:bg-gray-50'}`} onClick={() => toggleRole(r)}>
                  {r}
                </button>
              ))}
            </div>
            {errors.roles && <p className="text-xs text-red-600">{errors.roles.message}</p>}
          </div>
          <div className="flex justify-end gap-2 mt-2">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>Cancelar</Button>
            <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Guardando…' : 'Guardar'}</Button>
          </div>
        </form>
      </div>
    </div>
  );
}
