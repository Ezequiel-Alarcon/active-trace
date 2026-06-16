import { useQuery } from '@tanstack/react-query';
import { useMutation } from '@tanstack/react-query';
import { fetchTpsSinCorregir, uploadFinalizacionReport } from '../services/entregasApi';
import type { TpsSinCorregirResponse } from '../types/entregas';

export function useTpsSinCorregir(materiaId?: string) {
  return useQuery<TpsSinCorregirResponse>({
    queryKey: ['tps-sin-corregir', materiaId],
    queryFn: () => fetchTpsSinCorregir(materiaId),
    staleTime: 1000 * 60,
  });
}

export function useUploadFinalizacion() {
  return useMutation<void, Error, File>({
    mutationFn: (file) => uploadFinalizacionReport(file),
  });
}
