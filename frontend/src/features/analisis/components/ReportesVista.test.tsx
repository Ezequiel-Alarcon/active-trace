import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse, server } from '@/test/server';
import ReportesVista from './ReportesVista';
import React from 'react';

function makeTree(hasData = true) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  if (!hasData) {
    server.use(
      http.get('http://localhost:8000/api/reportes/materia/:materiaId', () =>
        HttpResponse.json({ materia_id: 'm-1', materia_nombre: '', cohorte_id: 'k-1', cohorte_nombre: '', total_alumnos: 0, alumnos: [] }),
      ),
    );
  }
  return (
    <QueryClientProvider client={qc}>
      <ReportesVista comisionId="c-1" />
    </QueryClientProvider>
  );
}

describe('ReportesVista', () => {
  it('4.4a — shows informative state when no data/activities selected', async () => {
    render(makeTree(false));
    await waitFor(() =>
      expect(screen.getByRole('status')).toBeInTheDocument(),
    );
    expect(screen.getByText(/Seleccioná una comisión/)).toBeInTheDocument();
  });

  it('4.4b — renders informative status (placeholder until comision→materia mapping)', () => {
    render(makeTree(true));
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});
