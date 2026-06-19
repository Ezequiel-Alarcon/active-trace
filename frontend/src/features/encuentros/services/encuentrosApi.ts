import { apiClient } from '@/shared/services/api';
import type { SlotResponse, InstanciaResponse, GuardiaResponse, EncuentroFilters } from '../types/encuentros';

export async function fetchEncuentros(filters?: EncuentroFilters): Promise<InstanciaResponse[]> {
  const params: Record<string, string> = {};
  if (filters?.materia) params.materia_id = filters.materia;
  if (filters?.estado) params.estado = filters.estado;
  if (filters?.fecha_desde) params.fecha_desde = filters.fecha_desde;
  if (filters?.fecha_hasta) params.fecha_hasta = filters.fecha_hasta;
  // Backend: GET /api/encuentros/instancias (not /api/encuentros)
  const response = await apiClient.get<InstanciaResponse[]>('/api/encuentros/instancias', { params });
  return response.data;
}

export async function fetchSlots(): Promise<SlotResponse[]> {
  const response = await apiClient.get<SlotResponse[]>('/api/encuentros/slots');
  return response.data;
}

export async function fetchGuardias(filters?: EncuentroFilters): Promise<GuardiaResponse[]> {
  const params: Record<string, string> = {};
  if (filters?.fecha_desde) params.fecha_desde = filters.fecha_desde;
  if (filters?.fecha_hasta) params.fecha_hasta = filters.fecha_hasta;
  const response = await apiClient.get<GuardiaResponse[]>('/api/guardias', { params });
  return response.data;
}

export async function exportarGuardias(): Promise<Blob> {
  const response = await apiClient.get('/api/guardias/exportar', { responseType: 'blob' });
  return response.data;
}
