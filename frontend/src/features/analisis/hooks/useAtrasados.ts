import { useQuery } from '@tanstack/react-query';
import { fetchAtrasados } from '../services/analisisApi';
import type { AtrasadosResponse } from '../types/analisis';

export function useAtrasados(materiaId?: string, cohorteId?: string) {
  return useQuery<AtrasadosResponse>({
    queryKey: ['atrasados', materiaId, cohorteId],
    queryFn: () => fetchAtrasados(materiaId, cohorteId),
    staleTime: 1000 * 60,
  });
}
