export type TareaEstado = 'Pendiente' | 'En progreso' | 'Resuelta' | 'Cancelada';

export interface TareaResponse {
  id: string;
  titulo: string;
  descripcion: string;
  materia_id?: string;
  materia_nombre?: string;
  docente_asignado_id: string;
  docente_asignado_nombre: string;
  docente_asignador_id: string;
  docente_asignador_nombre: string;
  estado: TareaEstado;
  created_at: string;
  updated_at: string;
}

export interface ComentarioResponse {
  id: string;
  tarea_id: string;
  autor_id: string;
  autor_nombre: string;
  texto: string;
  created_at: string;
}

export interface TareaFilters {
  estado?: TareaEstado;
  materia?: string;
  docente?: string;
  busqueda?: string;
}
