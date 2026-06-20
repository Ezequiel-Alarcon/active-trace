import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse, server } from '@/test/server';
import { AuthProvider } from '@/features/auth/components/AuthProvider';
import EncuentrosPage from './EncuentrosPage';

const sessionWithPermission = {
  user_id: 'u-1',
  email: 'coord@trace.com',
  tenant_id: 't-1',
  roles: ['COORDINADOR'],
  permissions: ['encuentros:gestionar'],
};

const sessionWithoutPermission: Session = {
  ...sessionWithPermission,
  permissions: [],
};

function makeTree(session = sessionWithPermission) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  server.use(
    http.get('http://localhost:8000/api/auth/session', () => HttpResponse.json(session)),
  );

  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <AuthProvider>
          <EncuentrosPage />
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('EncuentrosPage', () => {
  it('6.8a — shows tabs with Encuentros content', async () => {
    render(makeTree());
    await waitFor(() => {
      expect(screen.getByText('Crear slot')).toBeInTheDocument();
    });
    expect(screen.getByText('Slots')).toBeInTheDocument();
    expect(screen.getByText('Guardias')).toBeInTheDocument();
    expect(screen.getByText('Crear slot')).toBeInTheDocument();
    expect(screen.getByText('Crear único')).toBeInTheDocument();
  });

  it('6.8b — shows encuentros table by default', async () => {
    render(makeTree());
    await waitFor(() => {
      expect(screen.getByText('Matemáticas')).toBeInTheDocument();
      expect(screen.getByText('Pendiente')).toBeInTheDocument();
    });
  });

  it('6.8c — switches to Guardias tab and shows guardias', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await waitFor(() => screen.getByText('Guardias'));
    await user.click(screen.getByText('Guardias'));
    await waitFor(() => {
      expect(screen.getByText('Carlos López')).toBeInTheDocument();
    });
  });

  it('hides creation tabs when user lacks encuentros:gestionar', async () => {
    render(makeTree(sessionWithoutPermission));

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Encuentros' })).toBeInTheDocument();
    });

    expect(screen.queryByText('Crear slot')).not.toBeInTheDocument();
    expect(screen.queryByText('Crear único')).not.toBeInTheDocument();
  });
});
