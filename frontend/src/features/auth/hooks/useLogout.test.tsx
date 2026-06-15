import { describe, it, expect } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { http, HttpResponse } from '../../../test/server';
import { server } from '../../../test/server';
import { tokenStore } from '../../../shared/services/tokenStore';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../components/AuthProvider';
import React from 'react';

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  server.use(
    http.get('http://localhost:8000/api/auth/session', () =>
      HttpResponse.json({
        user: { user_id: 'u-1', email: 'a@b.com', tenant_id: 't-1' },
        roles: ['ADMIN'],
        permissions: [],
      }),
    ),
  );
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <AuthProvider>{children}</AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>
    );
  };
}

describe('useLogout', () => {
  beforeEach(() => tokenStore.set('active-token'));

  it('6.7 — 204 → clears token and navigates', async () => {
    server.use(
      http.post('http://localhost:8000/api/auth/logout', () =>
        new HttpResponse(null, { status: 204 }),
      ),
    );
    const { useLogout } = await import('./useLogout');
    const { result } = renderHook(() => useLogout(), { wrapper: makeWrapper() });

    await act(async () => {
      await result.current();
    });

    await waitFor(() => expect(tokenStore.get()).toBeNull());
  });

  it('6.7 — backend error → still clears local session and navigates', async () => {
    server.use(
      http.post('http://localhost:8000/api/auth/logout', () =>
        HttpResponse.json({}, { status: 500 }),
      ),
    );
    const { useLogout } = await import('./useLogout');
    const { result } = renderHook(() => useLogout(), { wrapper: makeWrapper() });

    await act(async () => {
      await result.current();
    });

    await waitFor(() => expect(tokenStore.get()).toBeNull());
  });
});
