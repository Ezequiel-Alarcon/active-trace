export interface MetricasResponse {
  total_alumnos: number;
  instancias_activas: number;
  reservas_activas: number;
  notas_registradas: number;
}

export interface ConvocatoriaResponse {
  id: string;
  materia_id: string;
  materia_nombre: string;
  instancia: string;
  dias_disponibles: string[];
  cupos: number;
  cupos_libres: number;
  convocados: number;
  reservas_activas: number;
  estado: string;
  created_at: string;
}

export interface ConvocatoriaCreate {
  materia_id: string;
  instancia: string;
  dias_disponibles: string[];
  cupos: number;
}

export interface ReservaResponse {
  id: string;
  convocatoria_id: string;
  alumno_id: string;
  alumno_nombre: string;
  dia: string;
  hora: string;
  estado: string;
}
