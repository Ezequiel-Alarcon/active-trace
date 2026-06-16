/**
 * Comision API service.
 *
 * TODO: (REVIEW) There is no dedicated backend endpoint to list comisiones for the
 * session. This service currently uses /api/reportes/materia/:materiaId to derive
 * context. A dedicated /api/comisiones endpoint would clarify the contract.
 * For now, comision data is derived from the analisis/atrasados response context.
 *
 * For the purpose of C-22 the feature uses a simplified endpoint:
 * GET /api/analisis/atrasados returns materia/cohorte context per alumno entry.
 * The ComisionSelector will list comisiones from a session-derived endpoint when
 * one is available. Until then, this is a placeholder.
 */

import { apiClient } from '@/shared/services/api';
import type { Comision } from '../types/comision';

/**
 * TODO: (FEAT) Replace with real backend endpoint when available.
 * Currently returns an empty list — comisiones are surfaced through context
 * gathered from calificaciones/analisis queries scoped to the session.
 */
export async function fetchComisionesDisponibles(): Promise<Comision[]> {
  const response = await apiClient.get<Comision[]>('/api/comisiones');
  return response.data;
}
