import { useQuery } from '@tanstack/react-query';
import { fetchCohortes } from '@/features/admin/services/estructuraApi';
import type { Cohorte } from '@/features/admin/types/estructura';

export function useCohortes(carreraId?: string) {
  return useQuery<Cohorte[]>({
    queryKey: ['encuentros-cohortes', carreraId ?? 'all'],
    queryFn: () => fetchCohortes(carreraId),
    staleTime: 1000 * 60 * 5,
  });
}
