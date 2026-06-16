import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse, server } from '@/test/server';
import NotasFinalesVista from './NotasFinalesVista';
import React from 'react';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <NotasFinalesVista />
    </QueryClientProvider>
  );
}

describe('NotasFinalesVista', () => {
  it('4.3a — renders notas finales per materia', async () => {
    render(makeTree());
    await waitFor(() =>
      expect(screen.getByText('Matemáticas')).toBeInTheDocument(),
    );
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('4.3b — shows empty state when no notas', async () => {
    server.use(
      http.get('http://localhost:8000/api/reportes/notas-finales', () =>
        HttpResponse.json({ total: 0, limit: 50, offset: 0, notas: [] }),
      ),
    );
    render(makeTree());
    await waitFor(() =>
      expect(screen.getByRole('status')).toBeInTheDocument(),
    );
    expect(screen.getByText(/No hay notas finales/)).toBeInTheDocument();
  });
});
