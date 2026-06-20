import { useQuery } from '@tanstack/react-query';
import { fetchMaterias } from '@/features/admin/services/estructuraApi';
import type { Materia } from '@/features/admin/types/estructura';

export function useMaterias() {
  return useQuery<Materia[]>({
    queryKey: ['encuentros-materias'],
    queryFn: fetchMaterias,
    staleTime: 1000 * 60 * 5,
  });
}
