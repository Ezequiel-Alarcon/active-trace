import { useQuery } from '@tanstack/react-query';
import { fetchNotasFinales } from '../services/analisisApi';
import type { NotasFinalesResponse } from '../types/analisis';

export function useNotasFinales(limit = 50, offset = 0) {
  return useQuery<NotasFinalesResponse>({
    queryKey: ['notas-finales', limit, offset],
    queryFn: () => fetchNotasFinales(limit, offset),
    staleTime: 1000 * 60,
  });
}
