import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/shared/services/api';
import type { Session } from '../types/session';

export const SESSION_QUERY_KEY = ['session'] as const;

async function fetchSession(): Promise<Session> {
  const response = await apiClient.get<Session>('/api/auth/session');
  return response.data;
}

export function useSession() {
  return useQuery({
    queryKey: SESSION_QUERY_KEY,
    queryFn: fetchSession,
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 min
  });
}
