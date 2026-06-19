export interface Carrera {
  id: string;
  codigo: string;
  nombre: string;
  estado: 'Activa' | 'Inactiva';
  created_at: string;
  updated_at: string;
}

export interface CreateCarreraRequest {
  codigo: string;
  nombre: string;
}

export interface UpdateCarreraRequest {
  codigo?: string;
  nombre?: string;
  estado?: 'Activa' | 'Inactiva';
}

export interface Cohorte {
  id: string;
  carrera_id: string;
  carrera_nombre: string;
  nombre: string;
  anio: number;
  vig_desde: string;
  vig_hasta: string | null;
  estado: string;
  created_at: string;
  updated_at: string;
}

export interface CreateCohorteRequest {
  carrera_id: string;
  nombre: string;
  anio: number;
  vig_desde: string;
  vig_hasta?: string | null;
}

export interface UpdateCohorteRequest {
  nombre?: string;
  anio?: number;
  vig_desde?: string;
  vig_hasta?: string | null;
  estado?: string;
}

export interface Materia {
  id: string;
  codigo: string;
  nombre: string;
  estado: string;
  created_at: string;
  updated_at: string;
}

export interface CreateMateriaRequest {
  codigo: string;
  nombre: string;
}

export interface UpdateMateriaRequest {
  codigo?: string;
  nombre?: string;
  estado?: string;
}
