import { useQuery } from '@tanstack/react-query';
import { fetchRanking } from '../services/analisisApi';
import type { RankingResponse } from '../types/analisis';

export function useRanking(materiaId: string | null) {
  return useQuery<RankingResponse>({
    queryKey: ['ranking', materiaId],
    queryFn: () => fetchRanking(materiaId!),
    enabled: Boolean(materiaId),
    staleTime: 1000 * 60,
  });
}
