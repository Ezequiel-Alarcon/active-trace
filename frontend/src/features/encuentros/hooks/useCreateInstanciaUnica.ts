import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createInstanciaUnica } from '../services/encuentrosApi';
import type {
  CreateInstanciaUnicaRequest,
  CreatedInstanciaUnicaResponse,
} from '../types/encuentros';

export function useCreateInstanciaUnica() {
  const queryClient = useQueryClient();

  return useMutation<CreatedInstanciaUnicaResponse, Error, CreateInstanciaUnicaRequest>({
    mutationFn: createInstanciaUnica,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['encuentros'] }),
  });
}
