import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createSlot } from '../services/encuentrosApi';
import type { CreateSlotRequest, CreatedSlotResponse } from '../types/encuentros';

export function useCreateSlot() {
  const queryClient = useQueryClient();

  return useMutation<CreatedSlotResponse, Error, CreateSlotRequest>({
    mutationFn: createSlot,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['slots'] }),
  });
}
