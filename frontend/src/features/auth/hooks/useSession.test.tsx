import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from '../../../test/server';
import { server } from '../../../test/server';
import { useSession } from './useSession';
import type { Session } from '../types/session';
import React from 'react';

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

const mockSession: Session = {
  user: { user_id: 'u-1', email: 'test@example.com', tenant_id: 't-1' },
  roles: ['COORDINADOR'],
  permissions: ['alumnos:ver', 'calificaciones:importar'],
};

describe('useSession', () => {
  it('returns user and permissions from the server bootstrap response', async () => {
    server.use(
      http.get('http://localhost:8000/api/auth/session', () => {
        return HttpResponse.json(mockSession);
      }),
    );

    const { result } = renderHook(() => useSession(), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.user.email).toBe('test@example.com');
    expect(result.current.data?.permissions).toContain('calificaciones:importar');
  });

  it('returns an error when the session endpoint fails', async () => {
    server.use(
      http.get('http://localhost:8000/api/auth/session', () => {
        return HttpResponse.json({}, { status: 401 });
      }),
    );

    const { result } = renderHook(() => useSession(), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.data).toBeUndefined();
  });
});
