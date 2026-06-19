import { useQuery } from '@tanstack/react-query';
import { fetchMonitorGeneral } from '../services/monitorApi';
import type { MonitoreoGeneralResponse, MonitorFilters } from '../types/monitor';

export function useMonitorGeneral(filters?: MonitorFilters) {
  return useQuery<MonitoreoGeneralResponse>({
    queryKey: ['monitor-general', filters],
    queryFn: () => fetchMonitorGeneral(filters),
    staleTime: 1000 * 60,
  });
}
