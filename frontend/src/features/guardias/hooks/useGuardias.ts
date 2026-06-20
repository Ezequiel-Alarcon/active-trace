import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchGuardias, createGuardia } from '../services/guardiasApi';
import type { GuardiaCreate, GuardiaFilters } from '../types/guardias';

export function useGuardias(filters?: GuardiaFilters) {
  return useQuery({
    queryKey: ['guardias', filters],
    queryFn: () => fetchGuardias(filters),
    staleTime: 60_000,
  });
}

export function useCreateGuardia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GuardiaCreate) => createGuardia(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guardias'] });
    },
  });
}
