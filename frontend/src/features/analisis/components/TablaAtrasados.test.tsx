import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse, server } from '@/test/server';
import TablaAtrasados from './TablaAtrasados';
import React from 'react';

function makeTree(props: Parameters<typeof TablaAtrasados>[0]) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <TablaAtrasados {...props} />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('TablaAtrasados', () => {
  it('4.1a — shows table with alumnos data', async () => {
    render(makeTree({ comisionId: 'c-1' }));
    await waitFor(() =>
      expect(screen.getByText('Ana García')).toBeInTheDocument(),
    );
    expect(screen.getByText('Atrasado')).toBeInTheDocument();
  });

  it('4.1b — shows empty state when no alumnos', async () => {
    server.use(
      http.get('http://localhost:8000/api/analisis/atrasados', () =>
        HttpResponse.json({ total: 0, limit: 50, offset: 0, alumnos: [] }),
      ),
    );
    render(makeTree({ comisionId: 'c-1' }));
    await waitFor(() =>
      expect(screen.getByRole('status')).toBeInTheDocument(),
    );
    expect(screen.getByText(/No hay alumnos atrasados/)).toBeInTheDocument();
  });

  it('6.1a — comunicar button disabled with no selection', async () => {
    const onSelect = vi.fn();
    render(makeTree({ comisionId: 'c-1', onSeleccionarDestinatarios: onSelect }));
    await waitFor(() => screen.getByText('Ana García'));
    expect(screen.getByText(/Comunicar seleccionados/)).toBeDisabled();
  });

  it('6.1b — comunicar button enabled after selecting an alumno', async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(makeTree({ comisionId: 'c-1', onSeleccionarDestinatarios: onSelect }));
    await waitFor(() => screen.getByText('Ana García'));
    await user.click(screen.getByRole('checkbox', { name: /Seleccionar Ana García/ }));
    expect(screen.getByText(/Comunicar seleccionados/)).not.toBeDisabled();
    await user.click(screen.getByText(/Comunicar seleccionados/));
    expect(onSelect).toHaveBeenCalledWith(['ana@test.com']);
  });
});
