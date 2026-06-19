import { apiClient } from '@/shared/services/api';
import type {
  LiquidacionPeriodoResponse,
  LiquidacionHistorialEntry,
  LiquidacionCierreResponse,
  SalarioBase,
  CreateSalarioBaseRequest,
  SalarioPlus,
  CreateSalarioPlusRequest,
} from '../types/liquidaciones';

export async function fetchLiquidacionPeriodo(
  cohorteId: string,
  periodo: string, // YYYY-MM format
): Promise<LiquidacionPeriodoResponse> {
  // Backend: POST /api/liquidaciones/calcular with body {cohorte_id, periodo}
  const response = await apiClient.post<LiquidacionPeriodoResponse>('/api/liquidaciones/calcular', {
    cohorte_id: cohorteId,
    periodo,
  });
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

// NOTE: GET /salarios/base and GET /salarios/plus do not exist in backend.
// Only POST /salarios/base (create base) and POST /salarios/plus (create plus) exist.
// The grilla salarial listing will require a future backend change.

export async function createSalarioBase(data: CreateSalarioBaseRequest): Promise<SalarioBase> {
  const response = await apiClient.post<SalarioBase>('/api/liquidaciones/salarios/base', data);
  return response.data;
}

export async function createSalarioPlus(data: CreateSalarioPlusRequest): Promise<SalarioPlus> {
  const response = await apiClient.post<SalarioPlus>('/api/liquidaciones/salarios/plus', data);
  return response.data;
}
