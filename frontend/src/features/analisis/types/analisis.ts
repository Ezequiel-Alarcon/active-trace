/**
 * Types for the analisis feature.
 * Mirrors AtrasadosResponse, RankingResponse, NotasFinalesResponse,
 * ReporteMateriaResponse from C-11 backend.
 *
 * TODO: (REVIEW) Backend uses permission "analisis:ver" but spec says "atrasados:ver".
 * Using "analisis:ver" to match the actual backend until clarified.
 *
 * TODO: (REVIEW) MonitoreoGeneralResponse.datos is list[dict[str, Any]] in backend —
 * cannot be fully typed without clarifying the exact shape. Using Record<string,unknown>[].
 */

export interface AlumnoAtrasado {
  usuario_id: string;
  email: string;
  nombre: string;
  materia_id: string;
  materia_nombre: string;
  asignacion_id: string | null;
  asignacion_nombre: string | null;
  estado: string;
  nota_actual: number | string | unknown[] | null;
  umbral_pct: number;
}

export interface AtrasadosResponse {
  total: number;
  limit: number;
  offset: number;
  alumnos: AlumnoAtrasado[];
}

export interface RankingEntry {
  posicion: number;
  usuario_id: string;
  nombre: string;
  email: string;
  cantidad_aprobadas: number;
  cantidad_totales: number;
  nota_promedio: number | null;
}

export interface RankingResponse {
  materia_id: string;
  materia_nombre: string;
  rankings: RankingEntry[];
}

export interface ActividadEstado {
  asignacion_id: string | null;
  asignacion_nombre: string | null;
  estado: string;
  nota: number | string | unknown[] | null;
  umbral_pct: number;
}

export interface AlumnoReporte {
  usuario_id: string;
  nombre: string;
  email: string;
  actividades: ActividadEstado[];
}

export interface ReporteMateriaResponse {
  materia_id: string;
  materia_nombre: string;
  cohorte_id: string;
  cohorte_nombre: string;
  total_alumnos: number;
  alumnos: AlumnoReporte[];
}

export interface NotasFinalesEntry {
  materia_id: string;
  materia_nombre: string;
  total_alumnos: number;
  aprobados: number;
  tasa_aprobacion: number;
  nota_promedio_global: number | null;
}

export interface NotasFinalesResponse {
  total: number;
  limit: number;
  offset: number;
  notas: NotasFinalesEntry[];
}
