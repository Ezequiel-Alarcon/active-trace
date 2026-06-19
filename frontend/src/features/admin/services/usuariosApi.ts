import { apiClient } from '@/shared/services/api';
import type {
  UsuarioTenant,
  CreateUsuarioRequest,
  UpdateUsuarioRequest,
} from '../types/usuarios';

export async function fetchUsuarios(busqueda?: string): Promise<UsuarioTenant[]> {
  const params: Record<string, string> = {};
  if (busqueda) params.busqueda = busqueda;
  const response = await apiClient.get<UsuarioTenant[]>('/api/admin/usuarios', { params });
  return response.data;
}

export async function createUsuario(data: CreateUsuarioRequest): Promise<UsuarioTenant> {
  const response = await apiClient.post<UsuarioTenant>('/api/admin/usuarios', data);
  return response.data;
}

export async function updateUsuario(
  id: string,
  data: UpdateUsuarioRequest,
): Promise<UsuarioTenant> {
  const response = await apiClient.patch<UsuarioTenant>(`/api/admin/usuarios/${id}`, data);
  return response.data;
}

export async function deleteUsuario(id: string): Promise<void> {
  await apiClient.delete(`/api/admin/usuarios/${id}`);
}
