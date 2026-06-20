import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchInbox, fetchThread, sendMensaje, replyMensaje } from '../services/mensajesApi';
import type { MensajeCreate, MensajeReply } from '../types/mensajes';

export function useInbox() {
  return useQuery({
    queryKey: ['mensajes-inbox'],
    queryFn: fetchInbox,
    staleTime: 30_000,
  });
}

export function useThread(hiloId: string | null) {
  return useQuery({
    queryKey: ['mensajes-thread', hiloId],
    queryFn: () => fetchThread(hiloId!),
    enabled: hiloId !== null,
    staleTime: 30_000,
  });
}

export function useSendMensaje() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: MensajeCreate) => sendMensaje(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mensajes-inbox'] });
    },
  });
}

export function useReplyMensaje() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ mensajeId, data }: { mensajeId: string; data: MensajeReply }) =>
      replyMensaje(mensajeId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mensajes-inbox'] });
      queryClient.invalidateQueries({ queryKey: ['mensajes-thread'] });
    },
  });
}
