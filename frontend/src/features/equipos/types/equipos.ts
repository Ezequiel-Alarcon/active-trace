export type EstadoEquipo = 'activo' | 'inactivo' | 'vencido';

export interface AsignacionResponse {
  id: string;
  materia_id: string;
  materia_nombre: string;
  carrera: string;
  cohorte: string;
  comisiones: string[];
  rol: string;
  docente_id: string;
  docente_nombre: string;
  vigencia_desde: string;
  vigencia_hasta: string;
  estado: EstadoEquipo;
}

export interface AsignacionMasivaRequest {
  docente_ids: string[];
  materia_id: string;
  carrera: string;
  cohorte: string;
  rol: string;
  vigencia_desde: string;
  vigencia_hasta: string;
}

export interface CloneRequest {
  origen_materia_id: string;
  origen_carrera: string;
  origen_cohorte: string;
  destino_materia_id: string;
  destino_carrera: string;
  destino_cohorte: string;
}

export interface VigenciaRequest {
  equipo_id: string;
  vigencia_desde: string;
  vigencia_hasta: string;
}

export interface EquipoFilters {
  estado?: EstadoEquipo;
  materia?: string;
  rol?: string;
  carrera?: string;
  cohorte?: string;
}
