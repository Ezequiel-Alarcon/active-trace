import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse, server } from '@/test/server';
import EntregasSinCorregir from './EntregasSinCorregir';
import React from 'react';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <EntregasSinCorregir comisionId="c-1" />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const CSV_FILE = new File(['id,nombre\n1,fin'], 'finalizacion.csv', { type: 'text/csv' });

describe('EntregasSinCorregir', () => {
  it('5.1a — upload triggers processing state', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await user.upload(screen.getByLabelText(/Reporte de finalización/), CSV_FILE);
    const btn = screen.getByText('Cruzar con calificaciones');
    expect(btn).not.toBeDisabled();
    await user.click(btn);
    await waitFor(() =>
      expect(screen.queryByText('Procesando…')).not.toBeInTheDocument(),
    );
  });

  it('5.2a — shows table with data', async () => {
    render(makeTree());
    await waitFor(() =>
      expect(screen.getByText('Matemáticas')).toBeInTheDocument(),
    );
  });

  it('5.2b — shows empty state when no entregas', async () => {
    server.use(
      http.get('http://localhost:8000/api/exportacion/tps-sin-corregir', () =>
        HttpResponse.json({ total: 0, alumnos: [] }),
      ),
    );
    render(makeTree());
    await waitFor(() =>
      expect(screen.getByRole('status')).toBeInTheDocument(),
    );
    expect(screen.getByText(/No se detectaron entregas/)).toBeInTheDocument();
  });

  it('5.3a — export button enabled when data exists', async () => {
    render(makeTree());
    // Wait for the data to load (table row shows up)
    await waitFor(() => screen.getByText('Matemáticas'));
    expect(screen.getByText('Exportar CSV')).not.toBeDisabled();
  });

  it('5.3b — export button disabled when no data', async () => {
    server.use(
      http.get('http://localhost:8000/api/exportacion/tps-sin-corregir', () =>
        HttpResponse.json({ total: 0, alumnos: [] }),
      ),
    );
    render(makeTree());
    await waitFor(() => screen.getByText('Exportar CSV'));
    expect(screen.getByText('Exportar CSV')).toBeDisabled();
  });
});
