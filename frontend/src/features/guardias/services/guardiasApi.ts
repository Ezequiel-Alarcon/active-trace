import { apiClient } from '@/shared/services/api';
import type { GuardiaCreate, GuardiaResponse, GuardiaFilters } from '../types/guardias';

export async function fetchGuardias(filters?: GuardiaFilters): Promise<GuardiaResponse[]> {
  const params: Record<string, string> = {};
  if (filters?.materia_id) params.materia_id = filters.materia_id;
  if (filters?.cohorte_id) params.cohorte_id = filters.cohorte_id;
  if (filters?.fecha_desde) params.fecha_desde = filters.fecha_desde;
  if (filters?.fecha_hasta) params.fecha_hasta = filters.fecha_hasta;
  const response = await apiClient.get<GuardiaResponse[]>('/api/guardias/', { params });
  return response.data;
}

export async function createGuardia(data: GuardiaCreate): Promise<GuardiaResponse> {
  const response = await apiClient.post<GuardiaResponse>('/api/guardias/', data);
  return response.data;
}
