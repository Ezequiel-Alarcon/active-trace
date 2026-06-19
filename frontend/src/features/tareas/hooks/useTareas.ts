import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchTareas, cambiarEstadoTarea, fetchComentarios,
  agregarComentario, delegarTarea,
} from '../services/tareasApi';
import type { TareaResponse, ComentarioResponse, TareaFilters } from '../types/tareas';

export function useTareas(filters?: TareaFilters) {
  return useQuery<TareaResponse[]>({
    queryKey: ['tareas', filters],
    queryFn: () => fetchTareas(filters),
    staleTime: 1000 * 60,
  });
}

export function useCambiarEstado() {
  const queryClient = useQueryClient();
  return useMutation<TareaResponse, Error, { id: string; estado: string }>({
    mutationFn: ({ id, estado }) => cambiarEstadoTarea(id, estado),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tareas'] });
    },
  });
}

export function useComentarios(tareaId: string) {
  return useQuery<ComentarioResponse[]>({
    queryKey: ['comentarios', tareaId],
    queryFn: () => fetchComentarios(tareaId),
    enabled: !!tareaId,
  });
}

export function useAgregarComentario(tareaId: string) {
  const queryClient = useQueryClient();
  return useMutation<ComentarioResponse, Error, string>({
    mutationFn: (texto) => agregarComentario(tareaId, texto),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comentarios', tareaId] });
    },
  });
}

export function useDelegarTarea() {
  const queryClient = useQueryClient();
  return useMutation<TareaResponse, Error, { id: string; docente_id: string }>({
    mutationFn: ({ id, docente_id }) => delegarTarea(id, docente_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tareas'] });
    },
  });
}
