import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchAvisos, crearAviso, editarAviso, eliminarAviso } from '../services/avisosApi';
import type { AvisoResponse, AvisoCreate, AvisoFilters } from '../types/avisos';

export function useAvisos(filters?: AvisoFilters) {
  return useQuery<AvisoResponse[]>({
    queryKey: ['avisos', filters],
    queryFn: () => fetchAvisos(filters),
    staleTime: 1000 * 60,
  });
}

export function useCrearAviso() {
  const queryClient = useQueryClient();
  return useMutation<AvisoResponse, Error, AvisoCreate>({
    mutationFn: crearAviso,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['avisos'] });
    },
  });
}

export function useEditarAviso() {
  const queryClient = useQueryClient();
  return useMutation<AvisoResponse, Error, { id: string; data: Partial<AvisoCreate> }>({
    mutationFn: ({ id, data }) => editarAviso(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['avisos'] });
    },
  });
}

export function useEliminarAviso() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: eliminarAviso,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['avisos'] });
    },
  });
}
