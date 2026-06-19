export interface ActionsPerDayEntry {
  fecha: string;
  acciones: number;
}

export interface ComunicacionStatusEntry {
  materia: string;
  docente: string;
  pendientes: number;
  enviando: number;
  ok: number;
  fallidos: number;
  cancelados: number;
}

export interface InteraccionEntry {
  materia: string;
  docente: string;
  tipo_accion: string;
  count: number;
}

export interface LastActionEntry {
  fecha_hora: string;
  usuario: string;
  materia: string;
  accion: string;
  ip: string;
}

export interface AuditLogEntry {
  id: string;
  fecha_hora: string;
  usuario: string;
  usuario_id: string;
  materia: string;
  materia_id: string;
  accion: string;
  filas_afectadas: number;
  ip: string;
  user_agent: string;
}

export interface AuditLogResponse {
  total: number;
  limit: number;
  offset: number;
  entries: AuditLogEntry[];
}

export interface AuditFilters {
  desde?: string;
  hasta?: string;
  materia_id?: string;
  actor_id?: string;
  estado?: string;
}
