export interface UsuarioTenant {
  id: string;
  nombre: string;
  apellidos: string;
  email: string;
  dni: string;
  cuil: string;
  roles: string[];
  estado: 'Activo' | 'Inactivo';
  created_at: string;
  updated_at: string;
}

export interface CreateUsuarioRequest {
  nombre: string;
  apellidos: string;
  email: string;
  dni: string;
  cuil: string;
  cbu?: string;
  alias_cbu?: string;
  banco?: string;
  regional?: string;
  roles: string[];
}

export interface UpdateUsuarioRequest {
  nombre?: string;
  apellidos?: string;
  email?: string;
  dni?: string;
  cuil?: string;
  cbu?: string;
  alias_cbu?: string;
  banco?: string;
  regional?: string;
  roles?: string[];
  estado?: 'Activo' | 'Inactivo';
}
