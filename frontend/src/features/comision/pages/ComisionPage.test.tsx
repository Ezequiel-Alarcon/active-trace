import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { http, HttpResponse, server, STUB_COMISIONES } from '@/test/server';
import { AuthProvider } from '@/features/auth/components/AuthProvider';
import ComisionPage from './ComisionPage';
import React from 'react';

const SESSION = {
  user: { user_id: 'u-1', email: 'prof@trace.com', tenant_id: 't-1' },
  roles: ['PROFESOR'],
  permissions: ['calificaciones:importar', 'analisis:ver', 'comunicacion:enviar'],
};

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  server.use(
    http.get('http://localhost:8000/api/auth/session', () =>
      HttpResponse.json(SESSION),
    ),
    http.get('http://localhost:8000/api/comisiones', () =>
      HttpResponse.json(STUB_COMISIONES),
    ),
  );
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/comision']}>
        <AuthProvider>
          <Routes>
            <Route path="/comision" element={<ComisionPage />}>
              <Route path="atrasados" element={<div>Vista atrasados</div>} />
              <Route path="ranking" element={<div>Vista ranking</div>} />
            </Route>
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('ComisionPage', () => {
  it('2.3a — shows selector guide without comision selected', async () => {
    render(makeTree());
    await waitFor(() =>
      expect(screen.getByText(/Seleccioná una materia y cohorte/)).toBeInTheDocument(),
    );
    expect(screen.queryByText('Atrasados')).not.toBeInTheDocument();
  });

  it('2.3b — shows nav tabs after selecting a comision', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await waitFor(() =>
      expect(screen.getByRole('combobox')).toBeInTheDocument(),
    );
    await user.selectOptions(screen.getByRole('combobox'), 'c-1');
    expect(screen.getByRole('navigation', { name: 'Vistas de comisión' })).toBeInTheDocument();
    expect(screen.getByText('Atrasados')).toBeInTheDocument();
  });

  it('2.3c — selected comision persists when switching between views', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await waitFor(() => expect(screen.getByRole('combobox')).toBeInTheDocument());
    await user.selectOptions(screen.getByRole('combobox'), 'c-1');
    // Navigate to Atrasados
    await user.click(screen.getByText('Atrasados'));
    await waitFor(() =>
      expect(screen.getByText('Vista atrasados')).toBeInTheDocument(),
    );
    // Navigate to Ranking
    await user.click(screen.getByText('Ranking'));
    await waitFor(() =>
      expect(screen.getByText('Vista ranking')).toBeInTheDocument(),
    );
    // Selector still shows the same value
    expect((screen.getByRole('combobox') as HTMLSelectElement).value).toBe('c-1');
  });
});
