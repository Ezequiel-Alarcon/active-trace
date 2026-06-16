import { useQuery } from '@tanstack/react-query';
import { fetchComisionesDisponibles } from '../services/comisionApi';
import type { Comision } from '../types/comision';

export const COMISIONES_QUERY_KEY = ['comisiones'] as const;

/**
 * Returns the list of comisiones available for the current session.
 *
 * TODO: (REVIEW) Depends on /api/comisiones which is not yet implemented in the
 * backend. Returns empty list until the endpoint exists.
 */
export function useComisionesDisponibles() {
  return useQuery<Comision[]>({
    queryKey: COMISIONES_QUERY_KEY,
    queryFn: fetchComisionesDisponibles,
    staleTime: 1000 * 60 * 5,
  });
}
