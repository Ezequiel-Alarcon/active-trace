/**
 * Types for the monitor-seguimiento feature.
 * Mirrors MonitoreoGeneralResponse from C-11 backend.
 *
 * TODO: (REVIEW) MonitoreoGeneralResponse.datos is list[dict[str, Any]] in backend.
 * Shape is not yet defined. Using Record<string, unknown>[] pending clarification.
 */

export interface MonitorEntry extends Record<string, unknown> {
  usuario_id?: string;
  nombre?: string;
  email?: string;
}

export interface MonitoreoGeneralResponse {
  datos: MonitorEntry[];
}

export interface MonitorFilters {
  alumno?: string;
  correo?: string;
  comision?: string;
  regional?: string;
  actividad?: string;
  minimo_cumplido?: number | null;
  fecha_desde?: string;
  fecha_hasta?: string;
  estado?: string;
  materia?: string;
  busqueda?: string;
}
