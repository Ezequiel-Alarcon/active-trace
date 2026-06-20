import { useQuery } from '@tanstack/react-query';
import { fetchEstadoAcademico } from '../services/alumnoApi';

export const useEstadoAcademico = () =>
  useQuery({ queryKey: ['alumno', 'estado'], queryFn: fetchEstadoAcademico });
