import { apiClient } from '@/shared/services/api';
import type { AvisoResponse, AvisoCreate, AvisoFilters } from '../types/avisos';

export async function fetchAvisos(filters?: AvisoFilters): Promise<AvisoResponse[]> {
  const params: Record<string, string> = {};
  if (filters?.alcance) params.alcance = filters.alcance;
  if (filters?.severidad) params.severidad = filters.severidad;
  if (filters?.estado) params.estado = filters.estado;
  if (filters?.fecha_desde) params.fecha_desde = filters.fecha_desde;
  if (filters?.fecha_hasta) params.fecha_hasta = filters.fecha_hasta;
  const response = await apiClient.get<AvisoResponse[]>('/api/avisos', { params });
  return response.data;
}

export async function crearAviso(data: AvisoCreate): Promise<AvisoResponse> {
  const response = await apiClient.post<AvisoResponse>('/api/avisos', data);
  return response.data;
}

export async function editarAviso(id: string, data: Partial<AvisoCreate>): Promise<AvisoResponse> {
  const response = await apiClient.put<AvisoResponse>(`/api/avisos/${id}`, data);
  return response.data;
}

export async function eliminarAviso(id: string): Promise<void> {
  await apiClient.delete(`/api/avisos/${id}`);
}
