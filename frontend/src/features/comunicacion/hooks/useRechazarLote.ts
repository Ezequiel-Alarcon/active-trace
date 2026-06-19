import { useMutation, useQueryClient } from '@tanstack/react-query';
import { rechazarLote } from '../services/comunicacionApi';

export function useRechazarLote() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (loteId) => rechazarLote(loteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lotes-pendientes'] });
    },
  });
}
