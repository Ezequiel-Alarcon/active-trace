import React, { createContext, useContext, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useSession, SESSION_QUERY_KEY } from '../hooks/useSession';
import { tokenStore } from '@/shared/services/tokenStore';
import { setLogoutCallback } from '@/shared/services/api';
import type { Session, LoginResponse } from '../types/session';


interface AuthContextValue {
  session: Session | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  hasPermission: (permission: string) => boolean;
  setSession: (loginResponse: LoginResponse) => void;
  clearSession: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const { data: session, isLoading } = useSession();

  const clearSession = useCallback(() => {
    tokenStore.clear();
    queryClient.removeQueries({ queryKey: SESSION_QUERY_KEY });
    queryClient.setQueryData(SESSION_QUERY_KEY, null);
  }, [queryClient]);

  // Wire logout callback for the API interceptor
  React.useEffect(() => {
    setLogoutCallback(() => {
      clearSession();
      // Navigation is handled by RequireAuth detecting the missing session
    });
  }, [clearSession]);

  const setSession = useCallback(
    (loginResponse: LoginResponse) => {
      tokenStore.set(loginResponse.access_token);
      // Invalidate so useSession refetches from /api/auth/session
      queryClient.invalidateQueries({ queryKey: SESSION_QUERY_KEY });
    },
    [queryClient],
  );

  const hasPermission = useCallback(
    (permission: string): boolean => {
      if (!session) return false;
      return session.permissions.includes(permission);
    },
    [session],
  );

  const value: AuthContextValue = {
    session: session ?? null,
    isAuthenticated: Boolean(session),
    isLoading,
    hasPermission,
    setSession,
    clearSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside <AuthProvider>');
  }
  return ctx;
}
