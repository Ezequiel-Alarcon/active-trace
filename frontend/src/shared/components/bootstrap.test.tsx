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

describe('8.4 — Bootstrap behavior', () => {
  it('app start with valid session → enters protected area', async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    server.use(
      http.get('http://localhost:8000/api/auth/session', () =>
        HttpResponse.json(validSession),
      ),
    );

    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={['/']}>
          <AuthProvider>
            <Routes>
              <Route element={<RequireAuth />}>
                <Route path="/" element={<div>Protected area</div>} />
              </Route>
              <Route path="/login" element={<div>Login page</div>} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await waitFor(() =>
      expect(screen.getByText('Protected area')).toBeInTheDocument(),
    );
    expect(screen.queryByText('Login page')).not.toBeInTheDocument();
  });

  it('app start with no session → redirects to login', async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    server.use(
      http.get('http://localhost:8000/api/auth/session', () =>
        HttpResponse.json({}, { status: 401 }),
      ),
    );

    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={['/']}>
          <AuthProvider>
            <Routes>
              <Route element={<RequireAuth />}>
                <Route path="/" element={<div>Protected area</div>} />
              </Route>
              <Route path="/login" element={<div>Login page</div>} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await waitFor(() =>
      expect(screen.getByText('Login page')).toBeInTheDocument(),
    );
    expect(screen.queryByText('Protected area')).not.toBeInTheDocument();
  });
});
