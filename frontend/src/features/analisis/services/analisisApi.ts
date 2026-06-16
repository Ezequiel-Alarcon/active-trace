import { apiClient } from '@/shared/services/api';
import type {
  AtrasadosResponse,
  RankingResponse,
  NotasFinalesResponse,
  ReporteMateriaResponse,
} from '../types/analisis';

/**
 * GET /api/analisis/atrasados
 * TODO: (REVIEW) Backend requires "analisis:ver" permission. Spec says "atrasados:ver".
 */
export async function fetchAtrasados(
  materiaId?: string,
  cohorteId?: string,
  limit = 50,
  offset = 0,
): Promise<AtrasadosResponse> {
  const params: Record<string, string | number> = { limit, offset };
  if (materiaId) params.materia_id = materiaId;
  if (cohorteId) params.cohorte_id = cohorteId;
  const response = await apiClient.get<AtrasadosResponse>('/api/analisis/atrasados', { params });
  return response.data;
}

/**
 * GET /api/analisis/ranking
 */
export async function fetchRanking(materiaId: string, limit = 50): Promise<RankingResponse> {
  const response = await apiClient.get<RankingResponse>('/api/analisis/ranking', {
    params: { materia_id: materiaId, limit },
  });
  return response.data;
}

/**
 * GET /api/reportes/notas-finales
 */
export async function fetchNotasFinales(limit = 50, offset = 0): Promise<NotasFinalesResponse> {
  const response = await apiClient.get<NotasFinalesResponse>('/api/reportes/notas-finales', {
    params: { limit, offset },
  });
  return response.data;
}

/**
 * GET /api/reportes/materia/:materiaId
 */
export async function fetchReporteMateria(materiaId: string): Promise<ReporteMateriaResponse> {
  const response = await apiClient.get<ReporteMateriaResponse>(
    `/api/reportes/materia/${materiaId}`,
  );
  return response.data;
}
