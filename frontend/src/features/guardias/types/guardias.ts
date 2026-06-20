export interface GuardiaCreate {
  materia_id: string;
  cohorte_id: string;
  fecha: string;
  hora_inicio: string;
  hora_fin: string;
  titulo?: string;
  observaciones?: string;
}

export interface GuardiaResponse {
  id: string;
  tenant_id: string;
  tutor_id: string;
  tutor_nombre?: string;
  materia_id: string;
  cohorte_id: string;
  fecha: string;
  hora_inicio: string;
  hora_fin: string;
  titulo?: string;
  observaciones?: string;
  created_at: string;
  updated_at: string;
}

export interface GuardiaFilters {
  materia_id?: string;
  cohorte_id?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
}
