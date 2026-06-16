/**
 * Types for the comunicacion feature.
 * Mirrors ComunicacionResponse, LoteStatusResponse, PreviewResponse from C-12 backend.
 */

export type ComunicacionEstado =
  | 'Pendiente'
  | 'Enviando'
  | 'Enviado'
  | 'Error'
  | 'Cancelado';

/** Terminal states — polling stops when all messages reach one of these. */
export const TERMINAL_ESTADOS: ComunicacionEstado[] = ['Enviado', 'Error', 'Cancelado'];

export interface ComunicacionCreate {
  asunto: string;
  cuerpo: string;
  destinatario: string;
  lote_id?: string | null;
}

export interface ComunicacionResponse {
  id: string;
  tenant_id: string;
  asunto: string;
  cuerpo: string;
  destinatario: string;
  estado: ComunicacionEstado;
  lote_id: string | null;
  error_detail: string | null;
  enviado_at: string | null;
  retry_count: number;
  created_at: string;
  updated_at: string;
}

export interface LoteStatusResponse {
  lote_id: string;
  tenant_id: string;
  total: number;
  pendientes: number;
  enviando: number;
  enviados: number;
  errores: number;
  cancelados: number;
}

export interface PreviewRequest {
  asunto: string;
  cuerpo: string;
  destinatario: string;
}

export interface PreviewResponse {
  asunto: string;
  cuerpo: string;
  destinatario: string;
}
