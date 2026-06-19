import { apiClient } from '@/shared/services/api';
import type {
  LiquidacionPeriodoResponse,
  LiquidacionHistorialEntry,
  LiquidacionCierreResponse,
  SalarioBase,
  CreateSalarioBaseRequest,
  UpdateSalarioBaseRequest,
  SalarioPlus,
  CreateSalarioPlusRequest,
  UpdateSalarioPlusRequest,
} from '../types/liquidaciones';

export async function fetchLiquidacionPeriodo(
  cohorteId?: string,
  mes?: string,
  docenteId?: string,
): Promise<LiquidacionPeriodoResponse> {
  const params: Record<string, string> = {};
  if (cohorteId) params.cohorte_id = cohorteId;
  if (mes) params.mes = mes;
  if (docenteId) params.docente_id = docenteId;
  const response = await apiClient.get<LiquidacionPeriodoResponse>('/api/liquidaciones', { params });
  return response.data;
}

export async function cerrarLiquidacion(periodo: string): Promise<LiquidacionCierreResponse> {
  const response = await apiClient.post<LiquidacionCierreResponse>('/api/liquidaciones/cerrar', { periodo });
  return response.data;
}

export async function fetchHistorial(): Promise<LiquidacionHistorialEntry[]> {
  const response = await apiClient.get<LiquidacionHistorialEntry[]>('/api/liquidaciones/historial');
  return response.data;
}

export async function fetchDetalleHistorial(
  historialId: string,
): Promise<LiquidacionPeriodoResponse> {
  const response = await apiClient.get<LiquidacionPeriodoResponse>(
    `/api/liquidaciones/historial/${historialId}`,
  );
  return response.data;
}

export async function fetchSalariosBase(): Promise<SalarioBase[]> {
  const response = await apiClient.get<SalarioBase[]>('/api/liquidaciones/salarios-base');
  return response.data;
}

export async function createSalarioBase(data: CreateSalarioBaseRequest): Promise<SalarioBase> {
  const response = await apiClient.post<SalarioBase>('/api/liquidaciones/salarios-base', data);
  return response.data;
}

export async function updateSalarioBase(
  id: string,
  data: UpdateSalarioBaseRequest,
): Promise<SalarioBase> {
  const response = await apiClient.patch<SalarioBase>(`/api/liquidaciones/salarios-base/${id}`, data);
  return response.data;
}

export async function deleteSalarioBase(id: string): Promise<void> {
  await apiClient.delete(`/api/liquidaciones/salarios-base/${id}`);
}

export async function fetchSalariosPlus(): Promise<SalarioPlus[]> {
  const response = await apiClient.get<SalarioPlus[]>('/api/liquidaciones/salarios-plus');
  return response.data;
}

export async function createSalarioPlus(data: CreateSalarioPlusRequest): Promise<SalarioPlus> {
  const response = await apiClient.post<SalarioPlus>('/api/liquidaciones/salarios-plus', data);
  return response.data;
}

export async function updateSalarioPlus(
  id: string,
  data: UpdateSalarioPlusRequest,
): Promise<SalarioPlus> {
  const response = await apiClient.patch<SalarioPlus>(`/api/liquidaciones/salarios-plus/${id}`, data);
  return response.data;
}

export async function deleteSalarioPlus(id: string): Promise<void> {
  await apiClient.delete(`/api/liquidaciones/salarios-plus/${id}`);
}
