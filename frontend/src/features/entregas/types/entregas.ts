/**
 * Types for the entregas-sin-corregir feature.
 * Mirrors TpsSinCorregirResponse from C-11 backend.
 *
 * TODO: (REVIEW) TpsSinCorregirEntry.alumnos is list[dict] in backend — no defined shape.
 * Using Record<string, unknown> until the backend schema is clarified.
 */

export interface TpSinCorregirEntry {
  usuario_id: string | null;
  materia_id: string;
  materia_nombre: string | null;
  /** Additional fields from the untyped backend list[dict]. */
  [key: string]: unknown;
}

export interface TpsSinCorregirResponse {
  total: number;
  alumnos: TpSinCorregirEntry[];
}
