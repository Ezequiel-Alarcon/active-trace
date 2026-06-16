import { useQuery } from '@tanstack/react-query';
import { fetchReporteMateria } from '../services/analisisApi';
import type { ReporteMateriaResponse } from '../types/analisis';

export function useReporteMateria(materiaId: string | null) {
  return useQuery<ReporteMateriaResponse>({
    queryKey: ['reporte-materia', materiaId],
    queryFn: () => fetchReporteMateria(materiaId!),
    enabled: Boolean(materiaId),
    staleTime: 1000 * 60,
  });
}
