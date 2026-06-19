export interface SlotResponse {
  id: string;
  materia_id: string;
  materia_nombre: string;
  dia: string;
  horario: string;
  fecha_inicio: string;
  cantidad_semanas: number;
  titulo: string;
  enlace: string;
}

export interface InstanciaResponse {
  id: string;
  materia_id: string;
  materia_nombre: string;
  docente_id: string;
  docente_nombre: string;
  dia: string;
  horario: string;
  enlace: string;
  estado: string;
  grabacion: string;
}

export interface GuardiaResponse {
  id: string;
  tutor_id: string;
  tutor_nombre: string;
  materia_id: string;
  materia_nombre: string;
  dia: string;
  horario: string;
  estado: string;
  comentarios: string;
}

export interface EncuentroFilters {
  materia?: string;
  docente?: string;
  estado?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
}
