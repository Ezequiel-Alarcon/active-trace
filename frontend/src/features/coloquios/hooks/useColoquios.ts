import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchMetricasColoquios, fetchConvocatorias, crearConvocatoria, fetchReservas } from '../services/coloquiosApi';
import type { MetricasResponse, ConvocatoriaResponse, ConvocatoriaCreate, ReservaResponse } from '../types/coloquios';

export function useMetricasColoquios() {
  return useQuery<MetricasResponse>({
    queryKey: ['coloquios-metrics'],
    queryFn: fetchMetricasColoquios,
    staleTime: 1000 * 60 * 2,
  });
}

export function useConvocatorias() {
  return useQuery<ConvocatoriaResponse[]>({
    queryKey: ['coloquios-convocatorias'],
    queryFn: fetchConvocatorias,
    staleTime: 1000 * 60,
  });
}

export function useCrearConvocatoria() {
  const queryClient = useQueryClient();
  return useMutation<ConvocatoriaResponse, Error, ConvocatoriaCreate>({
    mutationFn: crearConvocatoria,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coloquios-convocatorias'] });
    },
  });
}

export function useReservas(convocatoriaId: string) {
  return useQuery<ReservaResponse[]>({
    queryKey: ['coloquios-reservas', convocatoriaId],
    queryFn: () => fetchReservas(convocatoriaId),
    enabled: !!convocatoriaId,
  });
}
