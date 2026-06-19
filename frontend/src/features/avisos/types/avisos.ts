export type Alcance = 'Global' | 'PorMateria' | 'PorCohorte' | 'PorRol';
export type Severidad = 'Informativo' | 'Advertencia' | 'Urgente';
export type EstadoAviso = 'activo' | 'inactivo';

export interface AvisoResponse {
  id: string;
  titulo: string;
  cuerpo: string;
  alcance: Alcance;
  contexto_id?: string;
  roles_destinatarios: string[];
  severidad: Severidad;
  vigencia_desde: string;
  vigencia_hasta: string;
  orden_prioridad: number;
  estado: EstadoAviso;
  requiere_ack: boolean;
  created_at: string;
  updated_at: string;
}

export interface AvisoCreate {
  titulo: string;
  cuerpo: string;
  alcance: Alcance;
  contexto_id?: string;
  roles_destinatarios: string[];
  severidad: Severidad;
  vigencia_desde: string;
  vigencia_hasta: string;
  orden_prioridad?: number;
  requiere_ack?: boolean;
}

export interface AvisoFilters {
  alcance?: Alcance;
  severidad?: Severidad;
  estado?: EstadoAviso;
  fecha_desde?: string;
  fecha_hasta?: string;
}
