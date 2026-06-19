import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchLiquidacionPeriodo,
  cerrarLiquidacion,
  fetchHistorial,
  fetchDetalleHistorial,
} from '../services/liquidacionesApi';
import type { LiquidacionPeriodoResponse, LiquidacionHistorialEntry, LiquidacionCierreResponse } from '../types/liquidaciones';

export function useLiquidacionPeriodo(
  cohorteId?: string,
  periodo?: string, // YYYY-MM format
) {
  return useQuery<LiquidacionPeriodoResponse>({
    queryKey: ['liquidacion-periodo', cohorteId, periodo],
    queryFn: () => fetchLiquidacionPeriodo(cohorteId!, periodo!),
    enabled: Boolean(cohorteId) && Boolean(periodo),
    staleTime: 1000 * 60,
  });
}

export function useCerrarLiquidacion() {
  const queryClient = useQueryClient();

  return useMutation<LiquidacionCierreResponse, Error, string>({
    mutationFn: (periodo) => cerrarLiquidacion(periodo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['liquidacion-periodo'] });
      queryClient.invalidateQueries({ queryKey: ['liquidacion-historial'] });
    },
  });
}

export function useHistorial() {
  return useQuery<LiquidacionHistorialEntry[]>({
    queryKey: ['liquidacion-historial'],
    queryFn: fetchHistorial,
    staleTime: 1000 * 60,
  });
}

export function useDetalleHistorial(historialId: string | null) {
  return useQuery<LiquidacionPeriodoResponse>({
    queryKey: ['liquidacion-detalle-historial', historialId],
    queryFn: () => fetchDetalleHistorial(historialId!),
    enabled: Boolean(historialId),
    staleTime: 1000 * 60,
  });
}
