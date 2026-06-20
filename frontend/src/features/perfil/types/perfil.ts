export interface PerfilResponse {
  id: string;
  tenant_id: string;
  nombre: string;
  apellidos: string;
  email: string;
  dni: string;
  cuil: string;
  cbu: string;
  alias_cbu?: string;
  banco?: string;
  regional?: string;
  legajo?: string;
  legajo_profesional?: string;
  fecha_nacimiento?: string;
  genero?: string;
  observaciones?: string;
  facturante: boolean;
  created_at: string;
  updated_at: string;
}

export interface PerfilUpdate {
  nombre?: string;
  apellidos?: string;
  email?: string;
  dni?: string;
  cbu?: string;
  alias_cbu?: string;
  banco?: string;
  regional?: string;
  legajo?: string;
  legajo_profesional?: string;
  fecha_nacimiento?: string;
  genero?: string;
  observaciones?: string;
}
