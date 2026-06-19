import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchCarreras,
  createCarrera,
  updateCarrera,
  deleteCarrera,
  fetchCohortes,
  createCohorte,
  updateCohorte,
  deleteCohorte,
  fetchMaterias,
  createMateria,
  updateMateria,
  deleteMateria,
} from '../services/estructuraApi';
import type {
  Carrera,
  CreateCarreraRequest,
  UpdateCarreraRequest,
  Cohorte,
  CreateCohorteRequest,
  UpdateCohorteRequest,
  Materia,
  CreateMateriaRequest,
  UpdateMateriaRequest,
} from '../types/estructura';

export function useCarreras() {
  return useQuery<Carrera[]>({
    queryKey: ['admin-carreras'],
    queryFn: fetchCarreras,
    staleTime: 1000 * 60,
  });
}

export function useCreateCarrera() {
  const queryClient = useQueryClient();
  return useMutation<Carrera, Error, CreateCarreraRequest>({
    mutationFn: createCarrera,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-carreras'] }),
  });
}

export function useUpdateCarrera() {
  const queryClient = useQueryClient();
  return useMutation<Carrera, Error, { id: string; data: UpdateCarreraRequest }>({
    mutationFn: ({ id, data }) => updateCarrera(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-carreras'] }),
  });
}

export function useDeleteCarrera() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteCarrera,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-carreras'] }),
  });
}

export function useCohortes(carreraId?: string) {
  return useQuery<Cohorte[]>({
    queryKey: ['admin-cohortes', carreraId],
    queryFn: () => fetchCohortes(carreraId),
    enabled: Boolean(carreraId),
    staleTime: 1000 * 60,
  });
}

export function useCreateCohorte() {
  const queryClient = useQueryClient();
  return useMutation<Cohorte, Error, CreateCohorteRequest>({
    mutationFn: createCohorte,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-cohortes'] }),
  });
}

export function useUpdateCohorte() {
  const queryClient = useQueryClient();
  return useMutation<Cohorte, Error, { id: string; data: UpdateCohorteRequest }>({
    mutationFn: ({ id, data }) => updateCohorte(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-cohortes'] }),
  });
}

export function useDeleteCohorte() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteCohorte,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-cohortes'] }),
  });
}

export function useMaterias() {
  return useQuery<Materia[]>({
    queryKey: ['admin-materias'],
    queryFn: fetchMaterias,
    staleTime: 1000 * 60,
  });
}

export function useCreateMateria() {
  const queryClient = useQueryClient();
  return useMutation<Materia, Error, CreateMateriaRequest>({
    mutationFn: createMateria,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-materias'] }),
  });
}

export function useUpdateMateria() {
  const queryClient = useQueryClient();
  return useMutation<Materia, Error, { id: string; data: UpdateMateriaRequest }>({
    mutationFn: ({ id, data }) => updateMateria(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-materias'] }),
  });
}

export function useDeleteMateria() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteMateria,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-materias'] }),
  });
}
