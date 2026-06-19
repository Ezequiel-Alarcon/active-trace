import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import EstructuraPage from './EstructuraPage';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <EstructuraPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('EstructuraPage', () => {
  it('4.1a — renders tabs and shows carreras', async () => {
    render(makeTree());
    await waitFor(() => expect(screen.getByText(/Estructura académica/i)).toBeInTheDocument());
    expect(screen.getByText('Carreras')).toBeInTheDocument();
    expect(screen.getByText('Cohortes')).toBeInTheDocument();
    expect(screen.getByText('Materias')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText(/Licenciatura en Matemática/i)).toBeInTheDocument());
  });

  it('4.1b — clicking Agregar carrera opens modal', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await waitFor(() => expect(screen.getByText(/Estructura académica/i)).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: 'Agregar carrera' }));
    await waitFor(() => expect(screen.getByRole('heading', { name: /Agregar carrera/i })).toBeInTheDocument());
  });
});
