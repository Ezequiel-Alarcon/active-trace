import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from '../../../test/server';
import { server } from '../../../test/server';
import { AuthProvider, useAuth } from './AuthProvider';
import type { Session } from '../types/session';
import React from 'react';

const sessionWithPerms: Session = {
  user: { user_id: 'u-1', email: 'admin@trace.com', tenant_id: 't-1' },
  roles: ['ADMIN'],
  permissions: ['alumnos:ver', 'calificaciones:importar'],
};

function TestConsumer({ perm }: { perm: string }) {
  const { hasPermission, isAuthenticated } = useAuth();
  return (
    <div>
      <span data-testid="auth">{String(isAuthenticated)}</span>
      <span data-testid="perm">{String(hasPermission(perm))}</span>
    </div>
  );
}

function makeTree(sessionResponse: Session | null, perm: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  if (sessionResponse) {
    server.use(
      http.get('http://localhost:8000/api/auth/session', () =>
        HttpResponse.json(sessionResponse),
      ),
    );
  } else {
    server.use(
      http.get('http://localhost:8000/api/auth/session', () =>
        HttpResponse.json({}, { status: 401 }),
      ),
    );
  }
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <TestConsumer perm={perm} />
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe('AuthProvider / useAuth', () => {
  it('hasPermission returns true for a permission in the session', async () => {
    render(makeTree(sessionWithPerms, 'calificaciones:importar'));
    await waitFor(() =>
      expect(screen.getByTestId('perm').textContent).toBe('true'),
    );
    expect(screen.getByTestId('auth').textContent).toBe('true');
  });

  it('hasPermission returns false for a permission NOT in the session', async () => {
    render(makeTree(sessionWithPerms, 'liquidaciones:cerrar'));
    await waitFor(() =>
      expect(screen.getByTestId('perm').textContent).toBe('false'),
    );
  });

  it('hasPermission returns false when session is empty (no permissions)', async () => {
    const emptySession: Session = {
      ...sessionWithPerms,
      permissions: [],
    };
    render(makeTree(emptySession, 'alumnos:ver'));
    await waitFor(() =>
      expect(screen.getByTestId('perm').textContent).toBe('false'),
    );
  });

  it('isAuthenticated is false when session request fails', async () => {
    render(makeTree(null, 'anything'));
    await waitFor(() =>
      expect(screen.getByTestId('auth').textContent).toBe('false'),
    );
  });
});
