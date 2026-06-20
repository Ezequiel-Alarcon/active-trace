import { apiClient } from '@/shared/services/api';

export interface EvaluacionDisponible {
  id: string;
  materia_id: string;
  instancia: string;
  estado: string;
  convocados: number;
  reservas_activas: number;
  cupos_libres: number;
}

export interface MisReservasItem {
  reserva_id: string;
  evaluacion_id: string;
  materia: string | null;
  instancia: string;
  fecha_reserva: string;
  estado: string;
}

export const fetchEvaluacionesDisponibles = (): Promise<{ evaluaciones: EvaluacionDisponible[] }> =>
  apiClient.get<{ evaluaciones: EvaluacionDisponible[] }>('/api/coloquios/').then((r) => r.data);

export const fetchMisReservas = (): Promise<MisReservasItem[]> =>
  apiClient.get<MisReservasItem[]>('/api/coloquios/mis-reservas').then((r) => r.data);

export const cancelarReserva = (reservaId: string): Promise<void> =>
  apiClient.patch<void>(`/api/coloquios/reservas/${reservaId}/cancelar`).then((r) => r.data);
