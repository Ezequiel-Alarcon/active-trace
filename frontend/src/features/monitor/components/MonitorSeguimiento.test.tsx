import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse, server } from '@/test/server';
import MonitorSeguimiento from './MonitorSeguimiento';
import React from 'react';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MonitorSeguimiento />
    </QueryClientProvider>
  );
}

describe('MonitorSeguimiento', () => {
  it('7.1a — shows alumnos from session', async () => {
    render(makeTree());
    await waitFor(() =>
      expect(screen.getByText('Pedro')).toBeInTheDocument(),
    );
  });

  it('7.1b — shows empty state when no alumnos match', async () => {
    server.use(
      http.get('http://localhost:8000/api/monitores/seguimiento', () =>
        HttpResponse.json({ datos: [] }),
      ),
    );
    render(makeTree());
    await waitFor(() =>
      expect(screen.getByRole('status')).toBeInTheDocument(),
    );
    expect(screen.getByText(/No hay alumnos que coincidan/)).toBeInTheDocument();
  });

  it('7.2a — filter form sends combined filters to backend', async () => {
    const user = userEvent.setup();
    const capturedRequests: string[] = [];
    server.use(
      http.get('http://localhost:8000/api/monitores/seguimiento', ({ request }) => {
        capturedRequests.push(request.url);
        return HttpResponse.json({ datos: [] });
      }),
    );
    render(makeTree());
    await waitFor(() => screen.getByPlaceholderText('Comisión'));
    await user.type(screen.getByPlaceholderText('Comisión'), 'Mat');
    await user.click(screen.getByText('Filtrar'));
    await waitFor(() => {
      const filtered = capturedRequests.find((u) => u.includes('comision=Mat'));
      expect(filtered).toBeTruthy();
    });
  });

  it('7.3a — limpiar filtros resets the view without filters', async () => {
    const user = userEvent.setup();
    let callCount = 0;
    server.use(
      http.get('http://localhost:8000/api/monitores/seguimiento', () => {
        callCount++;
        return HttpResponse.json({ datos: [{ usuario_id: 'u-1', nombre: 'Pedro', email: 'pedro@test.com', comision: 'Mat 2024' }] });
      }),
    );
    render(makeTree());
    await waitFor(() => screen.getByPlaceholderText('Alumno'));
    await user.type(screen.getByPlaceholderText('Alumno'), 'Ana');
    await user.click(screen.getByText('Filtrar'));
    await user.click(screen.getByText('Limpiar filtros'));
    // Filter inputs are cleared
    expect((screen.getByPlaceholderText('Alumno') as HTMLInputElement).value).toBe('');
    await waitFor(() =>
      expect(screen.getByText('Pedro')).toBeInTheDocument(),
    );
  });
});
