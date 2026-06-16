/**
 * Calificaciones API service.
 * All requests go through apiClient (auth/refresh interceptors included).
 *
 * Upload note: multipart/form-data is set by the browser when using FormData —
 * do NOT manually set Content-Type, as Axios must include the boundary.
 * The request interceptor only sets Authorization; it does not override Content-Type
 * set by FormData, so auth/refresh is safe with binary bodies.
 */

import { apiClient } from '@/shared/services/api';
import type {
  CalificacionPreviewResponse,
  CalificacionConfirmResponse,
  UmbralMateriaRead,
  UmbralMateriaCreate,
} from '../types/calificaciones';

export type ImportType = 'grades' | 'completion';

/**
 * POST /api/calificaciones/import/preview
 * Parses a CSV file and returns a preview (no persistence).
 */
export async function previewImport(
  file: File,
  type: ImportType = 'grades',
): Promise<CalificacionPreviewResponse> {
  const form = new FormData();
  form.append('file', file);
  const response = await apiClient.post<CalificacionPreviewResponse>(
    `/api/calificaciones/import/preview?type=${type}`,
    form,
    // Let axios set Content-Type with the multipart boundary automatically
  );
  return response.data;
}

/**
 * POST /api/calificaciones/import/confirm
 * Persists rows from a preview token.
 */
export async function confirmImport(
  previewToken: string,
): Promise<CalificacionConfirmResponse> {
  const response = await apiClient.post<CalificacionConfirmResponse>(
    '/api/calificaciones/import/confirm',
    { preview_token: previewToken },
  );
  return response.data;
}

/**
 * GET /api/umbral-materia
 */
export async function fetchUmbrales(materiaId?: string): Promise<UmbralMateriaRead[]> {
  const params = materiaId ? { materia_id: materiaId } : {};
  const response = await apiClient.get<UmbralMateriaRead[]>('/api/umbral-materia', { params });
  return response.data;
}

/**
 * POST /api/umbral-materia
 */
export async function createUmbral(data: UmbralMateriaCreate): Promise<UmbralMateriaRead> {
  const response = await apiClient.post<UmbralMateriaRead>('/api/umbral-materia', data);
  return response.data;
}

/**
 * PUT /api/umbral-materia/:id
 */
export async function updateUmbral(
  id: string,
  data: Partial<UmbralMateriaCreate>,
): Promise<UmbralMateriaRead> {
  const response = await apiClient.put<UmbralMateriaRead>(`/api/umbral-materia/${id}`, data);
  return response.data;
}
