import { apiClient } from '@/shared/services/api';
import type { InboxThreadItem, MensajeCreate, MensajeReply, MensajeResponse } from '../types/mensajes';

export async function fetchInbox(): Promise<InboxThreadItem[]> {
  const response = await apiClient.get<InboxThreadItem[]>('/api/mensajes/inbox');
  return response.data;
}

export async function fetchThread(hiloId: string): Promise<MensajeResponse[]> {
  const response = await apiClient.get<MensajeResponse[]>(`/api/mensajes/inbox/${hiloId}`);
  return response.data;
}

export async function sendMensaje(data: MensajeCreate): Promise<MensajeResponse> {
  const response = await apiClient.post<MensajeResponse>('/api/mensajes/', data);
  return response.data;
}

export async function replyMensaje(mensajeId: string, data: MensajeReply): Promise<MensajeResponse> {
  const response = await apiClient.post<MensajeResponse>(`/api/mensajes/${mensajeId}/reply`, data);
  return response.data;
}
