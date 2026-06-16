import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/shared/services/api';
import type { Session } from '../types/session';

export const SESSION_QUERY_KEY = ['session'] as const;

/** Raw shape returned by the C-03 backend (flat, no nested `user` object). */
interface RawSession {
  user_id: string;
  email: string;
  tenant_id: string;
  roles: string[];
  permissions: string[];
}

async function fetchSession(): Promise<Session> {
  // TODO: (HACK C-07) Backend returns a flat payload {user_id, email, tenant_id, roles, permissions}.
  // Normalise it here into the nested Session shape so every consumer stays typed correctly.
  // Remove this adapter once the backend ships the nested `user` object.
  const response = await apiClient.get<RawSession>('/api/auth/session');
  const raw = response.data;
  return {
    user: {
      user_id: raw.user_id,
      email: raw.email,
      tenant_id: raw.tenant_id,
    },
    roles: raw.roles,
    permissions: raw.permissions,
  };
}

export function useSession() {
  return useQuery({
    queryKey: SESSION_QUERY_KEY,
    queryFn: fetchSession,
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 min
  });
}
