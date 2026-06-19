import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchMisEquipos, asignacionMasiva, clonarEquipo,
  actualizarVigencia, exportarEquipo,
} from '../services/equiposApi';
import type { AsignacionResponse, AsignacionMasivaRequest, CloneRequest, VigenciaRequest, EquipoFilters } from '../types/equipos';

export function useMisEquipos(filters?: EquipoFilters) {
  return useQuery<AsignacionResponse[]>({
    queryKey: ['mis-equipos', filters],
    queryFn: () => fetchMisEquipos(filters),
    staleTime: 1000 * 60,
  });
}

export function useAsignacionMasiva() {
  const queryClient = useQueryClient();
  return useMutation<{ creadas: number }, Error, AsignacionMasivaRequest>({
    mutationFn: asignacionMasiva,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mis-equipos'] });
    },
  });
}

export function useClonarEquipo() {
  const queryClient = useQueryClient();
  return useMutation<{ asignaciones: AsignacionResponse[] }, Error, CloneRequest>({
    mutationFn: clonarEquipo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mis-equipos'] });
    },
  });
}

export function useVigenciaEquipo() {
  const queryClient = useQueryClient();
  return useMutation<{ actualizadas: number }, Error, VigenciaRequest>({
    mutationFn: actualizarVigencia,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mis-equipos'] });
    },
  });
}

export function useExportarEquipo() {
  return useMutation<void, Error, string>({
    mutationFn: async (equipoId: string) => {
      const blob = await exportarEquipo(equipoId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `equipo-${equipoId}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    },
  });
}
