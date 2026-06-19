import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import { server, http, HttpResponse } from '@/test/server';
import AprobacionesPage from './AprobacionesPage';
import type { LotePendienteResponse } from '../types/comunicacion';

const STUB_LOTE: LotePendienteResponse = {
  lote_id: 'lote-1',
  tenant_id: 't-1',
  total: 5,
  pendientes: 5,
  enviando: 0,
  enviados: 0,
  errores: 0,
  cancelados: 0,
  asunto: 'Recordatorio de evaluación',
  cuerpo: 'Te informamos que tienes evaluaciones pendientes.',
  solicitado_por_nombre: 'Carlos López',
  destinatarios: ['ana@test.com', 'pedro@test.com'],
  created_at: '2024-01-01T10:00:00Z',
};

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <AprobacionesPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('AprobacionesPage', () => {
  it('renders header and pending lotes', async () => {
    render(makeTree());
    await waitFor(() => expect(screen.getByText(/Aprobaciones de Comunicaciones/i)).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText('Recordatorio de evaluación')).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText('5')).toBeInTheDocument());
  });

  it('shows empty state when no pending lotes', async () => {
    server.use(
      http.get('http://localhost:8000/api/comunicaciones/lotes', () =>
        HttpResponse.json([]),
      ),
    );
    render(makeTree());
    await waitFor(() => expect(screen.getByText('No hay comunicaciones pendientes de aprobación')).toBeInTheDocument());
  });

  it('shows loading state initially', () => {
    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false, staleTime: Infinity } },
    });
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <AprobacionesPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(screen.getByText('Cargando lote…')).toBeInTheDocument();
  });

  it('opens DetalleLoteModal on Ver click', async () => {
    render(makeTree());
    await waitFor(() => expect(screen.getByText('Recordatorio de evaluación')).toBeInTheDocument());
    const verBtn = screen.getByRole('button', { name: 'Ver' });
    verBtn.click();
    await waitFor(() => expect(screen.getByText('Detalle del lote')).toBeInTheDocument());
  });
});
