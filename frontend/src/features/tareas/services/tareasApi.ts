import { apiClient } from '@/shared/services/api';
import type { TareaResponse, ComentarioResponse, TareaFilters } from '../types/tareas';

export async function fetchTareas(filters?: TareaFilters): Promise<TareaResponse[]> {
  const params: Record<string, string> = {};
  if (filters?.estado) params.estado = filters.estado;
  if (filters?.materia) params.materia = filters.materia;
  if (filters?.docente) params.docente = filters.docente;
  if (filters?.busqueda) params.busqueda = filters.busqueda;
  const response = await apiClient.get<TareaResponse[]>('/api/tareas', { params });
  return response.data;
}

export async function cambiarEstadoTarea(id: string, estado: string): Promise<TareaResponse> {
  const response = await apiClient.patch<TareaResponse>(`/api/tareas/${id}/estado`, { estado });
  return response.data;
}

export async function fetchComentarios(tareaId: string): Promise<ComentarioResponse[]> {
  const response = await apiClient.get<ComentarioResponse[]>(`/api/tareas/${tareaId}/comentarios`);
  return response.data;
}

export async function agregarComentario(tareaId: string, texto: string): Promise<ComentarioResponse> {
  const response = await apiClient.post<ComentarioResponse>(`/api/tareas/${tareaId}/comentarios`, { texto });
  return response.data;
}

export async function delegarTarea(tareaId: string, docente_id: string): Promise<TareaResponse> {
  const response = await apiClient.post<TareaResponse>(`/api/tareas/${tareaId}/delegar`, { docente_id });
  return response.data;
}
