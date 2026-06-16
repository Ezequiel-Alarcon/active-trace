import { apiClient } from '@/shared/services/api';
import type { TpsSinCorregirResponse } from '../types/entregas';

/**
 * GET /api/exportacion/tps-sin-corregir
 * TODO: (REVIEW) This endpoint does not accept a completion report upload.
 * The spec says "upload reporte de finalizacion" but the backend only has a GET.
 * The upload flow may need a separate endpoint. Marking as REVIEW.
 */
export async function fetchTpsSinCorregir(materiaId?: string): Promise<TpsSinCorregirResponse> {
  const params: Record<string, string> = {};
  if (materiaId) params.materia_id = materiaId;
  const response = await apiClient.get<TpsSinCorregirResponse>(
    '/api/exportacion/tps-sin-corregir',
    { params },
  );
  return response.data;
}

/**
 * TODO: (REVIEW) No backend endpoint exists for uploading completion report.
 * Task 5.1 uploads a "reporte de finalización" but no such POST endpoint was found
 * in analisis.py or calificaciones.py. Using import/preview with type=completion
 * as the closest match (it accepts type=completion in calificaciones router).
 */
export async function uploadFinalizacionReport(file: File): Promise<void> {
  const form = new FormData();
  form.append('file', file);
  await apiClient.post('/api/calificaciones/import/preview?type=completion', form);
}
