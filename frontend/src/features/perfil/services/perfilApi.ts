import { apiClient } from '@/shared/services/api';
import type { PerfilResponse, PerfilUpdate } from '../types/perfil';

export async function fetchPerfil(): Promise<PerfilResponse> {
  const response = await apiClient.get<PerfilResponse>('/api/perfil/');
  return response.data;
}

export async function updatePerfil(data: PerfilUpdate): Promise<PerfilResponse> {
  const response = await apiClient.patch<PerfilResponse>('/api/perfil/', data);
  return response.data;
}
