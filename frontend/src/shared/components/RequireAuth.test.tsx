import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '@/features/auth/components/AuthProvider';
import { http, HttpResponse } from '../../test/server';
import { server } from '../../test/server';
import RequireAuth from './RequireAuth';
import React from 'react';
import type { Session } from '@/features/auth/types/session';

const validSession: Session = {
  user: { user_id: 'u-1', email: 'a@trace.com', tenant_id: 't-1' },
  roles: ['ADMIN'],
  permissions: ['alumnos:ver'],
};

function makeTree(sessionResponse: Session | null, initialPath = '/protected') {
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
      <MemoryRouter initialEntries={[initialPath]}>
        <AuthProvider>
          <Routes>
            <Route element={<RequireAuth />}>
              <Route path="/protected" element={<div>Protected content</div>} />
            </Route>
            <Route path="/login" element={<div>Login page</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('RequireAuth', () => {
  it('7.2 — no session → redirects to /login', async () => {
    render(makeTree(null));

    // After bootstrap fails, should navigate to login
    await waitFor(() =>
      expect(screen.getByText('Login page')).toBeInTheDocument(),
    );
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument();
  });

  it('7.2 — authenticated user sees the protected content', async () => {
    render(makeTree(validSession));

    await waitFor(() =>
      expect(screen.getByText('Protected content')).toBeInTheDocument(),
    );
    expect(screen.queryByText('Login page')).not.toBeInTheDocument();
  });
});
