import { useQuery } from '@tanstack/react-query';
import { fetchEncuentros, fetchSlots, fetchGuardias, exportarGuardias } from '../services/encuentrosApi';
import type { InstanciaResponse, SlotResponse, GuardiaResponse, EncuentroFilters } from '../types/encuentros';

export function useEncuentros(filters?: EncuentroFilters) {
  return useQuery<InstanciaResponse[]>({
    queryKey: ['encuentros', filters],
    queryFn: () => fetchEncuentros(filters),
    staleTime: 1000 * 60,
  });
}

export function useSlots() {
  return useQuery<SlotResponse[]>({
    queryKey: ['slots'],
    queryFn: fetchSlots,
    staleTime: 1000 * 60 * 5,
  });
}

export function useGuardias(filters?: EncuentroFilters) {
  return useQuery<GuardiaResponse[]>({
    queryKey: ['guardias', filters],
    queryFn: () => fetchGuardias(filters),
    staleTime: 1000 * 60,
  });
}

export async function downloadGuardiasExport() {
  const blob = await exportarGuardias();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'guardias.csv';
  a.click();
  window.URL.revokeObjectURL(url);
}
