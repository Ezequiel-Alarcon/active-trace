import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import UsuariosPage from './UsuariosPage';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <UsuariosPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('UsuariosPage', () => {
  it('4.2a — renders header and shows usuarios', async () => {
    render(makeTree());
    await waitFor(() => expect(screen.getByText(/Usuarios/i)).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText(/admin@trace.com/i)).toBeInTheDocument());
  });

  it('4.2b — opens modal on Agregar usuario click', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await waitFor(() => expect(screen.getByText(/Usuarios/i)).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: 'Agregar usuario' }));
    await waitFor(() => expect(screen.getByRole('heading', { name: /Agregar usuario/i })).toBeInTheDocument());
  });
});
