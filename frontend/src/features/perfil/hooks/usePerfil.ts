import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchPerfil, updatePerfil } from '../services/perfilApi';
import type { PerfilUpdate } from '../types/perfil';

export function usePerfil() {
  return useQuery({
    queryKey: ['perfil'],
    queryFn: fetchPerfil,
    staleTime: 5 * 60_000,
  });
}

export function useUpdatePerfil() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PerfilUpdate) => updatePerfil(data),
    onSuccess: (updated) => {
      queryClient.setQueryData(['perfil'], updated);
    },
  });
}
