import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse, server } from '@/test/server';
import ColoquiosPage from './ColoquiosPage';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ColoquiosPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('ColoquiosPage', () => {
  it('7.8a — shows KPI cards with metrics', async () => {
    render(makeTree());
    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument();
    });
    expect(screen.getByText('Total alumnos')).toBeInTheDocument();
    expect(screen.getByText('Instancias activas')).toBeInTheDocument();
    expect(screen.getAllByText('Reservas activas').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Notas registradas')).toBeInTheDocument();
  });

  it('7.8b — shows convocatorias table', async () => {
    render(makeTree());
    await waitFor(() => {
      expect(screen.getByText('Matemáticas')).toBeInTheDocument();
      expect(screen.getByText('1er Parcial')).toBeInTheDocument();
    });
  });

  it('7.8c — new convocatoria opens form', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await waitFor(() => screen.getByText('Nueva convocatoria'));
    await user.click(screen.getByText('Nueva convocatoria'));
    expect(screen.getByText('Nueva convocatoria')).toBeInTheDocument();
    expect(screen.getByLabelText('ID Materia')).toBeInTheDocument();
  });
});
