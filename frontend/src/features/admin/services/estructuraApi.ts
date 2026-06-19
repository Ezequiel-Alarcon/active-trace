import { apiClient } from '@/shared/services/api';
import type {
  Carrera,
  CreateCarreraRequest,
  UpdateCarreraRequest,
  Cohorte,
  CreateCohorteRequest,
  UpdateCohorteRequest,
  Materia,
  CreateMateriaRequest,
  UpdateMateriaRequest,
} from '../types/estructura';

export async function fetchCarreras(): Promise<Carrera[]> {
  const response = await apiClient.get<Carrera[]>('/api/admin/carreras');
  return response.data;
}

export async function createCarrera(data: CreateCarreraRequest): Promise<Carrera> {
  const response = await apiClient.post<Carrera>('/api/admin/carreras', data);
  return response.data;
}

export async function updateCarrera(id: string, data: UpdateCarreraRequest): Promise<Carrera> {
  const response = await apiClient.patch<Carrera>(`/api/admin/carreras/${id}`, data);
  return response.data;
}

export async function deleteCarrera(id: string): Promise<void> {
  await apiClient.delete(`/api/admin/carreras/${id}`);
}

export async function fetchCohortes(carreraId?: string): Promise<Cohorte[]> {
  const params: Record<string, string> = {};
  if (carreraId) params.carrera_id = carreraId;
  const response = await apiClient.get<Cohorte[]>('/api/admin/cohortes', { params });
  return response.data;
}

export async function createCohorte(data: CreateCohorteRequest): Promise<Cohorte> {
  const response = await apiClient.post<Cohorte>('/api/admin/cohortes', data);
  return response.data;
}

export async function updateCohorte(id: string, data: UpdateCohorteRequest): Promise<Cohorte> {
  const response = await apiClient.patch<Cohorte>(`/api/admin/cohortes/${id}`, data);
  return response.data;
}

export async function deleteCohorte(id: string): Promise<void> {
  await apiClient.delete(`/api/admin/cohortes/${id}`);
}

export async function fetchMaterias(): Promise<Materia[]> {
  const response = await apiClient.get<Materia[]>('/api/admin/materias');
  return response.data;
}

export async function createMateria(data: CreateMateriaRequest): Promise<Materia> {
  const response = await apiClient.post<Materia>('/api/admin/materias', data);
  return response.data;
}

export async function updateMateria(id: string, data: UpdateMateriaRequest): Promise<Materia> {
  const response = await apiClient.patch<Materia>(`/api/admin/materias/${id}`, data);
  return response.data;
}

export async function deleteMateria(id: string): Promise<void> {
  await apiClient.delete(`/api/admin/materias/${id}`);
}
