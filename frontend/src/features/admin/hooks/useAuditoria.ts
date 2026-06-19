import { useQuery } from '@tanstack/react-query';
import {
  fetchActionsPerDay,
  fetchComunicacionStatus,
  fetchInteractions,
  fetchLastActions,
  fetchAuditLog,
} from '../services/auditoriaApi';
import type {
  ActionsPerDayEntry,
  ComunicacionStatusEntry,
  InteraccionEntry,
  LastActionEntry,
  AuditLogEntry,
} from '../types/auditoria';

export function useActionsPerDay(desde?: string, hasta?: string) {
  return useQuery<ActionsPerDayEntry[]>({
    queryKey: ['audit-actions-per-day', desde, hasta],
    queryFn: () => fetchActionsPerDay(desde, hasta),
    staleTime: 1000 * 60,
  });
}

export function useComunicacionStatus(materiaId?: string, desde?: string, hasta?: string) {
  return useQuery<ComunicacionStatusEntry[]>({
    queryKey: ['audit-comunicacion-status', materiaId, desde, hasta],
    queryFn: () => fetchComunicacionStatus(materiaId, desde, hasta),
    staleTime: 1000 * 60,
  });
}

export function useInteractions(materiaId?: string, desde?: string, hasta?: string) {
  return useQuery<InteraccionEntry[]>({
    queryKey: ['audit-interactions', materiaId, desde, hasta],
    queryFn: () => fetchInteractions(materiaId, desde, hasta),
    staleTime: 1000 * 60,
  });
}

export function useLastActions(limit = 10) {
  return useQuery<LastActionEntry[]>({
    queryKey: ['audit-last-actions', limit],
    queryFn: () => fetchLastActions(limit),
    staleTime: 1000 * 60,
  });
}

export function useAuditLog(
  limit = 50,
  offset = 0,
  filters?: { desde?: string; hasta?: string; materia_id?: string; actor_id?: string; estado?: string },
) {
  return useQuery<{ total: number; limit: number; offset: number; entries: AuditLogEntry[] }>({
    queryKey: ['audit-log', limit, offset, filters],
    queryFn: () => fetchAuditLog(limit, offset, filters),
    staleTime: 1000 * 30,
  });
}
