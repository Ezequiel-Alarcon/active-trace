/**
 * Types for the calificaciones feature.
 * Mirrors CalificacionPreviewResponse, CalificacionConfirmResponse from C-10 backend.
 */

export interface CalificacionPreviewRow {
  usuario_id: string | null;
  materia_id: string;
  asignacion_id: string | null;
  nota: unknown;
  valid: boolean;
  warnings: string[];
}

export interface CalificacionPreviewResponse {
  preview_token: string;
  rows: CalificacionPreviewRow[];
  total: number;
  filename: string;
}

export interface CalificacionConfirmResponse {
  persisted: number;
  skipped: number;
  failed: number;
}

/** Distinct actividad (asignacion) extracted from preview rows for selection UI. */
export interface ActividadDetectada {
  asignacion_id: string;
  label: string;
}

export interface UmbralMateriaRead {
  id: string;
  materia_id: string;
  asignacion_id: string | null;
  umbral_pct: number;
  created_at: string;
  updated_at: string;
}

export interface UmbralMateriaCreate {
  materia_id: string;
  asignacion_id: string | null;
  umbral_pct: number;
}
