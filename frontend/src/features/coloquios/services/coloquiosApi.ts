import { apiClient } from '@/shared/services/api';
import type { MetricasResponse, ConvocatoriaResponse, ConvocatoriaCreate, ReservaResponse } from '../types/coloquios';

export async function fetchMetricasColoquios(): Promise<MetricasResponse> {
  const response = await apiClient.get<MetricasResponse>('/api/coloquios/metricas');
  return response.data;
}

export async function fetchConvocatorias(): Promise<ConvocatoriaResponse[]> {
  const response = await apiClient.get<ConvocatoriaResponse[]>('/api/coloquios/convocatorias');
  return response.data;
}

export async function crearConvocatoria(data: ConvocatoriaCreate): Promise<ConvocatoriaResponse> {
  const response = await apiClient.post<ConvocatoriaResponse>('/api/coloquios/convocatorias', data);
  return response.data;
}

export async function fetchReservas(convocatoriaId: string): Promise<ReservaResponse[]> {
  const response = await apiClient.get<ReservaResponse[]>(`/api/coloquios/reservas?convocatoria_id=${convocatoriaId}`);
  return response.data;
}
