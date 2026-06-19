import { useMutation, useQuery } from '@tanstack/react-query';
import { aprobarLote, enqueueMensajes, fetchLoteStatus, fetchLotesPendientes, previewMensaje, rechazarLote } from '../services/comunicacionApi';
import { TERMINAL_ESTADOS } from '../types/comunicacion';
import type {
  ComunicacionCreate,
  ComunicacionResponse,
  LotePendienteResponse,
  LoteStatusResponse,
  PreviewRequest,
  PreviewResponse,
} from '../types/comunicacion';

export function usePreviewMensaje() {
  return useMutation<PreviewResponse, Error, PreviewRequest>({
    mutationFn: (data) => previewMensaje(data),
  });
}

export function useEnqueueMensajes() {
  return useMutation<ComunicacionResponse[], Error, ComunicacionCreate[]>({
    mutationFn: (mensajes) => enqueueMensajes(mensajes),
  });
}

/**
 * Polling hook for lote status.
 * Stops polling when all terminal counts add up to total.
 * Poll interval: 4 seconds.
 */
export function useLoteStatus(loteId: string | null) {
  return useQuery<LoteStatusResponse>({
    queryKey: ['lote-status', loteId],
    queryFn: () => fetchLoteStatus(loteId!),
    enabled: Boolean(loteId),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 4000;
      const terminales = data.enviados + data.errores + data.cancelados;
      if (terminales >= data.total && data.total > 0) return false;
      return 4000;
    },
    staleTime: 0,
  });
}

export function useLotesPendientes() {
  return useQuery<LotePendienteResponse[]>({
    queryKey: ['lotes-pendientes'],
    queryFn: fetchLotesPendientes,
    refetchInterval: 30_000, // refresh every 30s so other sessions' approve/reject actions are visible
  });
}
