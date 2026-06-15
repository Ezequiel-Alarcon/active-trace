import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '@/features/auth/components/AuthProvider';
import { http, HttpResponse } from '../../test/server';
import { server } from '../../test/server';
import RequirePermission from './RequirePermission';
import React from 'react';
import type { Session } from '@/features/auth/types/session';

function makeTree(permissions: string[], requiredPerm: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const session: Session = {
    user: { user_id: 'u-1', email: 'a@trace.com', tenant_id: 't-1' },
    roles: ['COORDINADOR'],
    permissions,
  };
  server.use(
    http.get('http://localhost:8000/api/auth/session', () =>
      HttpResponse.json(session),
    ),
  );
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <AuthProvider>
          <RequirePermission permission={requiredPerm}>
            <div>Contenido protegido</div>
          </RequirePermission>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('RequirePermission', () => {
  it('7.3 — user WITH the required permission sees the content', async () => {
    render(makeTree(['calificaciones:importar'], 'calificaciones:importar'));
    await waitFor(() =>
      expect(screen.getByText('Contenido protegido')).toBeInTheDocument(),
    );
    expect(screen.queryByText('Acceso denegado')).not.toBeInTheDocument();
  });

  it('7.3 — user WITHOUT the required permission sees Forbidden403', async () => {
    render(makeTree(['alumnos:ver'], 'liquidaciones:cerrar'));
    await waitFor(() =>
      expect(screen.getByText('Acceso denegado')).toBeInTheDocument(),
    );
    expect(screen.queryByText('Contenido protegido')).not.toBeInTheDocument();
  });

  it('7.3 — empty permission set blocks all routes (fail-closed)', async () => {
    render(makeTree([], 'alumnos:ver'));
    await waitFor(() =>
      expect(screen.getByText('Acceso denegado')).toBeInTheDocument(),
    );
    expect(screen.queryByText('Contenido protegido')).not.toBeInTheDocument();
  });
});
