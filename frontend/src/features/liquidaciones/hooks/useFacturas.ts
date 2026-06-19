import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchFacturas, createFactura, marcarAbonada } from '../services/facturasApi';
import type { Factura, CreateFacturaRequest } from '../types/liquidaciones';

export function useFacturas(
  docenteId?: string,
  estado?: string,
  desde?: string,
  hasta?: string,
) {
  return useQuery<Factura[]>({
    queryKey: ['facturas', docenteId, estado, desde, hasta],
    queryFn: () => fetchFacturas(docenteId, estado, desde, hasta),
    staleTime: 1000 * 60,
  });
}

export function useCreateFactura() {
  const queryClient = useQueryClient();
  return useMutation<Factura, Error, CreateFacturaRequest>({
    mutationFn: createFactura,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['facturas'] }),
  });
}

export function useMarcarAbonada() {
  const queryClient = useQueryClient();
  return useMutation<Factura, Error, string>({
    mutationFn: marcarAbonada,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['facturas'] }),
  });
}
