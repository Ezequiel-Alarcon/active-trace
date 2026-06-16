import { useMutation } from '@tanstack/react-query';
import { previewImport, confirmImport, type ImportType } from '../services/calificacionesApi';
import type { CalificacionPreviewResponse, CalificacionConfirmResponse } from '../types/calificaciones';

interface PreviewVars {
  file: File;
  type?: ImportType;
}

/**
 * Hook for managing the calificaciones import flow.
 * Phase 1: upload file → get preview (preview mutation)
 * Phase 2: confirm preview token → persist (confirm mutation)
 */
export function usePreviewImport() {
  return useMutation<CalificacionPreviewResponse, Error, PreviewVars>({
    mutationFn: ({ file, type }) => previewImport(file, type),
  });
}

export function useConfirmImport() {
  return useMutation<CalificacionConfirmResponse, Error, string>({
    mutationFn: (previewToken) => confirmImport(previewToken),
  });
}
