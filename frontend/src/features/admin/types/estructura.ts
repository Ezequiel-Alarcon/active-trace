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

// TODO: (BUG) El backend CohorteResponse no tiene campo 'carrera_nombre'.
// El campo existe en el servicio pero no en el schema de respuesta.
// El frontend espera carrera_nombre que el backend no devuelve.
// Ver backend/app/schemas/estructura.py:CohorteResponse
export interface Cohorte {
  id: string;
  carrera_id: string;
  carrera_nombre: string; // TODO: (FIX) Verificar si el backend realmente devuelve este campo
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
