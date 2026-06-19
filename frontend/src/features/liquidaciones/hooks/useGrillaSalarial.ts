import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createSalarioBase, createSalarioPlus } from '../services/liquidacionesApi';
import type {
  SalarioBase,
  SalarioPlus,
  CreateSalarioBaseRequest,
  CreateSalarioPlusRequest,
} from '../types/liquidaciones';

// NOTE: Backend only has POST /salarios/base and POST /salarios/plus.
// GET, PATCH, DELETE for salarios are not implemented.
// useSalariosBase, useSalariosPlus, useUpdateSalarioBase, useUpdateSalarioPlus,
// useDeleteSalarioBase, useDeleteSalarioPlus are non-functional until backend adds those endpoints.

export function useCreateSalarioBase() {
  const queryClient = useQueryClient();
  return useMutation<SalarioBase, Error, CreateSalarioBaseRequest>({
    mutationFn: createSalarioBase,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['salarios-base'] }),
  });
}

export function useCreateSalarioPlus() {
  const queryClient = useQueryClient();
  return useMutation<SalarioPlus, Error, CreateSalarioPlusRequest>({
    mutationFn: createSalarioPlus,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['salarios-plus'] }),
  });
}
