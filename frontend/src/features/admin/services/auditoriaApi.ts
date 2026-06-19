import { apiClient } from '@/shared/services/api';
import type {
  ActionsPerDayEntry,
  ComunicacionStatusEntry,
  InteraccionEntry,
  LastActionEntry,
  AuditLogEntry,
} from '../types/auditoria';

export async function fetchActionsPerDay(
  desde?: string,
  hasta?: string,
): Promise<ActionsPerDayEntry[]> {
  const params: Record<string, string> = {};
  if (desde) params.desde = desde;
  if (hasta) params.hasta = hasta;
  const response = await apiClient.get<ActionsPerDayEntry[]>('/api/audit/metrics/actions-per-day', { params });
  return response.data;
}

export async function fetchComunicacionStatus(
  materiaId?: string,
  desde?: string,
  hasta?: string,
): Promise<ComunicacionStatusEntry[]> {
  const params: Record<string, string> = {};
  if (materiaId) params.materia_id = materiaId;
  if (desde) params.desde = desde;
  if (hasta) params.hasta = hasta;
  const response = await apiClient.get<ComunicacionStatusEntry[]>('/api/audit/metrics/comunicacion-status', { params });
  return response.data;
}

export async function fetchInteractions(
  materiaId?: string,
  desde?: string,
  hasta?: string,
): Promise<InteraccionEntry[]> {
  const params: Record<string, string> = {};
  if (materiaId) params.materia_id = materiaId;
  if (desde) params.desde = desde;
  if (hasta) params.hasta = hasta;
  const response = await apiClient.get<InteraccionEntry[]>('/api/audit/metrics/interactions', { params });
  return response.data;
}

export async function fetchLastActions(limit = 10): Promise<LastActionEntry[]> {
  const response = await apiClient.get<LastActionEntry[]>('/api/audit/metrics/last-actions', {
    params: { limit },
  });
  return response.data;
}

export async function fetchAuditLog(
  limit = 50,
  offset = 0,
  filters?: { desde?: string; hasta?: string; materia_id?: string; actor_id?: string; estado?: string },
): Promise<{ total: number; limit: number; offset: number; entries: AuditLogEntry[] }> {
  const params: Record<string, string | number> = { limit, offset };
  if (filters?.desde) params.desde = filters.desde;
  if (filters?.hasta) params.hasta = filters.hasta;
  if (filters?.materia_id) params.materia_id = filters.materia_id;
  if (filters?.actor_id) params.actor_id = filters.actor_id;
  if (filters?.estado) params.estado = filters.estado;
  // TODO: (BUG) El frontend llama /api/audit/log pero el backend mountpea el router en /api/audit
  // por lo que el endpoint real es /audit/log. Hay inconsistencia en el prefjo.
  // Ver backend/app/api/v1/main_router.py — audit_router se mountpea directo en /api/audit
  // pero el path del router es /log, entonces debería ser /audit/log (correcto).
  // Solo marcar si realmente falla — puede que esté bien si el include_router usa prefix.
  const response = await apiClient.get('/api/audit/log', { params });
  return response.data;
}
