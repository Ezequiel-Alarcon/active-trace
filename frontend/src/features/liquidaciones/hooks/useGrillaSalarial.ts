import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchSalariosBase,
  createSalarioBase,
  updateSalarioBase,
  deleteSalarioBase,
  fetchSalariosPlus,
  createSalarioPlus,
  updateSalarioPlus,
  deleteSalarioPlus,
} from '../services/liquidacionesApi';
import type {
  SalarioBase,
  CreateSalarioBaseRequest,
  UpdateSalarioBaseRequest,
  SalarioPlus,
  CreateSalarioPlusRequest,
  UpdateSalarioPlusRequest,
} from '../types/liquidaciones';

export function useSalariosBase() {
  return useQuery<SalarioBase[]>({
    queryKey: ['salarios-base'],
    queryFn: fetchSalariosBase,
    staleTime: 1000 * 60,
  });
}

export function useCreateSalarioBase() {
  const queryClient = useQueryClient();
  return useMutation<SalarioBase, Error, CreateSalarioBaseRequest>({
    mutationFn: createSalarioBase,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['salarios-base'] }),
  });
}

export function useUpdateSalarioBase() {
  const queryClient = useQueryClient();
  return useMutation<SalarioBase, Error, { id: string; data: UpdateSalarioBaseRequest }>({
    mutationFn: ({ id, data }) => updateSalarioBase(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['salarios-base'] }),
  });
}

export function useDeleteSalarioBase() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteSalarioBase,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['salarios-base'] }),
  });
}

export function useSalariosPlus() {
  return useQuery<SalarioPlus[]>({
    queryKey: ['salarios-plus'],
    queryFn: fetchSalariosPlus,
    staleTime: 1000 * 60,
  });
}

export function useCreateSalarioPlus() {
  const queryClient = useQueryClient();
  return useMutation<SalarioPlus, Error, CreateSalarioPlusRequest>({
    mutationFn: createSalarioPlus,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['salarios-plus'] }),
  });
}

export function useUpdateSalarioPlus() {
  const queryClient = useQueryClient();
  return useMutation<SalarioPlus, Error, { id: string; data: UpdateSalarioPlusRequest }>({
    mutationFn: ({ id, data }) => updateSalarioPlus(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['salarios-plus'] }),
  });
}

export function useDeleteSalarioPlus() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteSalarioPlus,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['salarios-plus'] }),
  });
}
