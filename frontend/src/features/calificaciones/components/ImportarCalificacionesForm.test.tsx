import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse, server } from '@/test/server';
import ImportarCalificacionesForm from './ImportarCalificacionesForm';
import React from 'react';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ImportarCalificacionesForm comisionId="c-1" />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const CSV_FILE = new File(['email,nota\nana@test.com,8'], 'notas.csv', { type: 'text/csv' });

describe('ImportarCalificacionesForm', () => {
  it('3.3a — renders preview with activities after upload', async () => {
    const user = userEvent.setup();
    render(makeTree());
    const input = screen.getByLabelText(/Archivo de calificaciones/);
    await user.upload(input, CSV_FILE);
    await user.click(screen.getByText('Ver preview'));
    await waitFor(() =>
      expect(screen.getByText(/notas\.csv/)).toBeInTheDocument(),
    );
    // activity a-1 is detected
    expect(screen.getByText('a-1')).toBeInTheDocument();
  });

  it('3.3b — preview does not trigger computation (confirm button is visible but not auto-submitted)', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await user.upload(screen.getByLabelText(/Archivo de calificaciones/), CSV_FILE);
    await user.click(screen.getByText('Ver preview'));
    await waitFor(() => screen.getByText(/Confirmar y analizar/));
    // Confirm has NOT been clicked — no status message
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('3.4a — confirm button is disabled when no activity is selected', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await user.upload(screen.getByLabelText(/Archivo de calificaciones/), CSV_FILE);
    await user.click(screen.getByText('Ver preview'));
    await waitFor(() => screen.getByLabelText('a-1'));
    // Deselect the only activity
    await user.click(screen.getByLabelText('a-1'));
    expect(screen.getByText('Confirmar y analizar')).toBeDisabled();
  });

  it('3.5a — umbral defaults to 60', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await user.upload(screen.getByLabelText(/Archivo de calificaciones/), CSV_FILE);
    await user.click(screen.getByText('Ver preview'));
    await waitFor(() => screen.getByLabelText(/Umbral de aprobación/));
    const input = screen.getByLabelText(/Umbral de aprobación/) as HTMLInputElement;
    expect(input.value).toBe('60');
  });

  it('3.5b — umbral 150 shows validation error', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await user.upload(screen.getByLabelText(/Archivo de calificaciones/), CSV_FILE);
    await user.click(screen.getByText('Ver preview'));
    await waitFor(() => screen.getByLabelText(/Umbral de aprobación/));
    await user.clear(screen.getByLabelText(/Umbral de aprobación/));
    await user.type(screen.getByLabelText(/Umbral de aprobación/), '150');
    await user.click(screen.getByText('Confirmar y analizar'));
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/≤ 100/),
    );
  });

  it('3.5c — confirm calls backend and shows success', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await user.upload(screen.getByLabelText(/Archivo de calificaciones/), CSV_FILE);
    await user.click(screen.getByText('Ver preview'));
    await waitFor(() => screen.getByText('Confirmar y analizar'));
    await user.click(screen.getByText('Confirmar y analizar'));
    await waitFor(() =>
      expect(screen.getByRole('status')).toHaveTextContent(/Importación completada/),
    );
  });

  it('3.2b — backend error shows error message', async () => {
    server.use(
      http.post('http://localhost:8000/api/calificaciones/import/preview', () =>
        HttpResponse.json({ detail: 'Formato inválido' }, { status: 400 }),
      ),
    );
    const user = userEvent.setup();
    render(makeTree());
    await user.upload(screen.getByLabelText(/Archivo de calificaciones/), CSV_FILE);
    await user.click(screen.getByText('Ver preview'));
    await waitFor(() =>
      expect(screen.getByRole('alert')).toBeInTheDocument(),
    );
  });
});
