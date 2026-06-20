export interface InboxThreadItem {
  hilo_id: string;
  remitente_id: string;
  destinatario_id: string;
  ultimo_asunto: string;
  ultimo_cuerpo: string;
  leido: boolean;
  ultima_actividad: string;
}

export interface MensajeCreate {
  asunto: string;
  cuerpo: string;
  destinatario_id: string;
  hilo_id?: string;
}

export interface MensajeReply {
  asunto: string;
  cuerpo: string;
}

export interface MensajeResponse {
  id: string;
  tenant_id: string;
  asunto: string;
  cuerpo: string;
  remitente_id: string;
  destinatario_id: string;
  hilo_id: string;
  padre_id?: string;
  leido_at?: string;
  created_at: string;
  updated_at: string;
}
