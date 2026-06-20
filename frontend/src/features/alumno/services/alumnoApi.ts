import { apiClient } from '@/shared/services/api';

export interface CalificacionItem {
  materia_id: string;
  materia_codigo: string;
  materia_nombre: string;
  nota: number | string | null;
  aprobado: boolean | null;
  origen: string;
}

export interface EstadoAcademicoResponse {
  usuario_id: string;
  calificaciones: CalificacionItem[];
}

export const fetchEstadoAcademico = (): Promise<EstadoAcademicoResponse> =>
  apiClient.get<EstadoAcademicoResponse>('/api/alumno/estado').then((r) => r.data);
