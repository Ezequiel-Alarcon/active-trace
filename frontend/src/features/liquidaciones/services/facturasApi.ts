import { apiClient } from '@/shared/services/api';
import type { Factura, CreateFacturaRequest } from '../types/liquidaciones';

export async function fetchFacturas(
  docenteId?: string,
  estado?: string,
  desde?: string,
  hasta?: string,
): Promise<Factura[]> {
  const params: Record<string, string> = {};
  if (docenteId) params.docente_id = docenteId;
  if (estado) params.estado = estado;
  if (desde) params.desde = desde;
  if (hasta) params.hasta = hasta;
  const response = await apiClient.get<Factura[]>('/api/facturas', { params });
  return response.data;
}

export async function createFactura(data: CreateFacturaRequest): Promise<Factura> {
  const response = await apiClient.post<Factura>('/api/facturas', data);
  return response.data;
}

export async function marcarAbonada(id: string): Promise<Factura> {
  const response = await apiClient.patch<Factura>(`/api/facturas/${id}`, { estado: 'Abonada' });
  return response.data;
}
