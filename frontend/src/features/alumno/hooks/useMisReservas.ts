import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchMisReservas, cancelarReserva } from '../services/misReservasApi';

export const useMisReservas = () =>
  useQuery({ queryKey: ['alumno', 'mis-reservas'], queryFn: fetchMisReservas });

export const useCancelarReserva = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: cancelarReserva,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alumno', 'mis-reservas'] }),
  });
};
