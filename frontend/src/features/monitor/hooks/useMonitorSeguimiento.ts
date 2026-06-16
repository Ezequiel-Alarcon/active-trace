import { useQuery } from '@tanstack/react-query';
import { fetchMonitorSeguimiento } from '../services/monitorApi';
import type { MonitoreoGeneralResponse, MonitorFilters } from '../types/monitor';

export function useMonitorSeguimiento(filters?: MonitorFilters) {
  return useQuery<MonitoreoGeneralResponse>({
    queryKey: ['monitor-seguimiento', filters],
    queryFn: () => fetchMonitorSeguimiento(filters),
    staleTime: 1000 * 60,
  });
}
