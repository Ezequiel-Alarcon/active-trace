// TODO: (BUG) El hook useUsuarios devuelve UsuarioTenant[] que incluye dni, cuil, cbu.
// Según ARQUITECTURA.md §5.4 estos campos son PII y deben estar cifrados en el backend.
// Si el backend los devuelve sin cifrar, es una violación de seguridad.
// El frontend los muestra directamente sin descifrar.
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchUsuarios, createUsuario, updateUsuario, deleteUsuario } from '../services/usuariosApi';
import type {
  UsuarioTenant,
  CreateUsuarioRequest,
  UpdateUsuarioRequest,
} from '../types/usuarios';

export function useUsuarios(busqueda?: string) {
  return useQuery<UsuarioTenant[]>({
    queryKey: ['admin-usuarios', busqueda],
    queryFn: () => fetchUsuarios(busqueda),
    staleTime: 1000 * 60,
  });
}

export function useCreateUsuario() {
  const queryClient = useQueryClient();
  return useMutation<UsuarioTenant, Error, CreateUsuarioRequest>({
    mutationFn: createUsuario,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-usuarios'] }),
  });
}

export function useUpdateUsuario() {
  const queryClient = useQueryClient();
  return useMutation<UsuarioTenant, Error, { id: string; data: UpdateUsuarioRequest }>({
    mutationFn: ({ id, data }) => updateUsuario(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-usuarios'] }),
  });
}

export function useDeleteUsuario() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteUsuario,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-usuarios'] }),
  });
}
