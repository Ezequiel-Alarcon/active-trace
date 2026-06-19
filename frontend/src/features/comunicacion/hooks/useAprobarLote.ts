import { useMutation, useQueryClient } from '@tanstack/react-query';
import { aprobarLote } from '../services/comunicacionApi';

export function useAprobarLote() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (loteId) => aprobarLote(loteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lotes-pendientes'] });
    },
  });
}
