import { apiClient } from '@/shared/services/api';
import type { MonitoreoGeneralResponse, MonitorFilters } from '../types/monitor';

/**
 * GET /api/monitores/seguimiento
 * Returns alumnos assigned to the current session user (TUTOR/PROFESOR).
 * Scope is enforced server-side from the session.
 */
export async function fetchMonitorSeguimiento(
  filters?: MonitorFilters,
): Promise<MonitoreoGeneralResponse> {
  const params: Record<string, string | number> = {};
  if (filters?.alumno) params.alumno = filters.alumno;
  if (filters?.correo) params.correo = filters.correo;
  if (filters?.comision) params.comision = filters.comision;
  if (filters?.regional) params.regional = filters.regional;
  if (filters?.actividad) params.actividad = filters.actividad;
  if (filters?.minimo_cumplido != null) params.minimo_cumplido = filters.minimo_cumplido;
  if (filters?.fecha_desde) params.fecha_desde = filters.fecha_desde;
  if (filters?.fecha_hasta) params.fecha_hasta = filters.fecha_hasta;
  const response = await apiClient.get<MonitoreoGeneralResponse>('/api/monitores/seguimiento', {
    params,
  });
  return response.data;
}

export async function fetchMonitorGeneral(
  filters?: MonitorFilters,
): Promise<MonitoreoGeneralResponse> {
  const params: Record<string, string | number> = {};
  if (filters?.materia) params.materia = filters.materia;
  if (filters?.regional) params.regional = filters.regional;
  if (filters?.comision) params.comision = filters.comision;
  if (filters?.busqueda) params.busqueda = filters.busqueda;
  if (filters?.estado) params.estado = filters.estado;
  const response = await apiClient.get<MonitoreoGeneralResponse>('/api/monitores/general', {
    params,
  });
  return response.data;
}
