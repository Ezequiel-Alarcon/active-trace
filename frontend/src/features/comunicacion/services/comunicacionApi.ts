import { apiClient } from '@/shared/services/api';
import type {
  ComunicacionCreate,
  ComunicacionResponse,
  LoteStatusResponse,
  PreviewRequest,
  PreviewResponse,
} from '../types/comunicacion';

/**
 * POST /api/comunicaciones/preview
 * Renders personalized message without persisting.
 */
export async function previewMensaje(data: PreviewRequest): Promise<PreviewResponse> {
  const response = await apiClient.post<PreviewResponse>('/api/comunicaciones/preview', data);
  return response.data;
}

/**
 * POST /api/comunicaciones
 * Enqueues messages. Returns list of ComunicacionResponse (each in Pendiente).
 */
export async function enqueueMensajes(
  mensajes: ComunicacionCreate[],
): Promise<ComunicacionResponse[]> {
  const response = await apiClient.post<ComunicacionResponse[]>('/api/comunicaciones', mensajes);
  return response.data;
}

/**
 * GET /api/comunicaciones/lotes/:loteId
 * Returns status counts for all messages in a lote.
 */
export async function fetchLoteStatus(loteId: string): Promise<LoteStatusResponse> {
  const response = await apiClient.get<LoteStatusResponse>(
    `/api/comunicaciones/lotes/${loteId}`,
  );
  return response.data;
}
