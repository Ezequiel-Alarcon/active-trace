import { apiClient } from '@/shared/services/api';
import type { AsignacionResponse, AsignacionMasivaRequest, CloneRequest, VigenciaRequest, EquipoFilters } from '../types/equipos';

export async function fetchMisEquipos(filters?: EquipoFilters): Promise<AsignacionResponse[]> {
  const params: Record<string, string> = {};
  if (filters?.estado) params.estado = filters.estado;
  if (filters?.materia) params.materia = filters.materia;
  if (filters?.rol) params.rol = filters.rol;
  if (filters?.carrera) params.carrera = filters.carrera;
  if (filters?.cohorte) params.cohorte = filters.cohorte;
  const response = await apiClient.get<AsignacionResponse[]>('/api/equipos/mis-equipos', { params });
  return response.data;
}

export async function asignacionMasiva(data: AsignacionMasivaRequest): Promise<{ creadas: number }> {
  const response = await apiClient.post<{ creadas: number }>('/api/equipos/asignacion-masiva', data);
  return response.data;
}

export async function clonarEquipo(data: CloneRequest): Promise<{ asignaciones: AsignacionResponse[] }> {
  const response = await apiClient.post<{ asignaciones: AsignacionResponse[] }>('/api/equipos/clonar', data);
  return response.data;
}

export async function actualizarVigencia(data: VigenciaRequest): Promise<{ actualizadas: number }> {
  const response = await apiClient.patch<{ actualizadas: number }>('/api/equipos/vigencia', data);
  return response.data;
}

export async function exportarEquipo(equipoId: string): Promise<Blob> {
  const response = await apiClient.get(`/api/equipos/exportar/${equipoId}`, { responseType: 'blob' });
  return response.data;
}
