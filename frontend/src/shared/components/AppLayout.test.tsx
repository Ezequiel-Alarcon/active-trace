import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '@/features/auth/components/AuthProvider';
import { http, HttpResponse } from '../../test/server';
import { server } from '../../test/server';
import AppLayout from './AppLayout';
import React from 'react';
import type { Session } from '@/features/auth/types/session';

const sessionWithAlumnos: Session = {
  user: { user_id: 'u-1', email: 'coord@trace.com', tenant_id: 't-1' },
  roles: ['COORDINADOR'],
  permissions: ['alumnos:ver'],
};

const sessionWithoutAlumnos: Session = {
  ...sessionWithAlumnos,
  permissions: [],
};

function makeTree(session: Session, initialPath = '/') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  server.use(
    http.get('http://localhost:8000/api/auth/session', () =>
      HttpResponse.json(session),
    ),
  );
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initialPath]}>
        <AuthProvider>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/" element={<div>Home content</div>} />
            </Route>
            <Route path="/login" element={<div>Login page</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('AppLayout', () => {
  it('8.1 — renders header, nav, and outlet for authenticated routes', async () => {
    render(makeTree(sessionWithAlumnos));
    await waitFor(() =>
      expect(screen.getByText('Home content')).toBeInTheDocument(),
    );
    expect(screen.getByText('Active Trace')).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Navegación principal' })).toBeInTheDocument();
  });

  it('7.4 — menu shows items the user has permission for', async () => {
    render(makeTree(sessionWithAlumnos));
    await waitFor(() =>
      expect(screen.getByText('Inicio')).toBeInTheDocument(),
    );
  });

  it('7.4 — menu does NOT show items the user lacks permission for', async () => {
    render(makeTree(sessionWithoutAlumnos));
    await waitFor(() =>
      expect(screen.getByText('Active Trace')).toBeInTheDocument(),
    );
    expect(screen.queryByText('Inicio')).not.toBeInTheDocument();
  });

  it('8.2 — 404 page renders for unknown routes', async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    server.use(
      http.get('http://localhost:8000/api/auth/session', () =>
        HttpResponse.json(sessionWithAlumnos),
      ),
    );
    const { default: NotFound404 } = await import('./NotFound404');
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={['/nonexistent']}>
          <AuthProvider>
            <Routes>
              <Route element={<AppLayout />}>
                <Route path="/" element={<div>Home</div>} />
                <Route path="*" element={<NotFound404 />} />
              </Route>
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );
    await waitFor(() =>
      expect(screen.getByText('Página no encontrada')).toBeInTheDocument(),
    );
  });
});
