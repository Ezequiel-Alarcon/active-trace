import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse, server } from '@/test/server';
import TrackingComunicacion from './TrackingComunicacion';
import React from 'react';

function makeTree(loteId: string) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, refetchInterval: false } },
  });
  return (
    <QueryClientProvider client={qc}>
      <TrackingComunicacion loteId={loteId} />
    </QueryClientProvider>
  );
}

describe('TrackingComunicacion', () => {
  it('6.4a — shows pending state initially', async () => {
    render(makeTree('lote-1'));
    await waitFor(() => screen.getByText('Pendiente'));
    // 1 pending
    const cells = screen.getAllByText('1');
    expect(cells.length).toBeGreaterThan(0);
  });

  it('6.4b — shows completed state when all messages are terminal', async () => {
    server.use(
      http.get('http://localhost:8000/api/comunicaciones/lotes/:loteId', () =>
        HttpResponse.json({
          lote_id: 'lote-1',
          tenant_id: 't-1',
          total: 1,
          pendientes: 0,
          enviando: 0,
          enviados: 1,
          errores: 0,
          cancelados: 0,
        }),
      ),
    );
    render(makeTree('lote-1'));
    await waitFor(() =>
      expect(screen.getByText(/Envío completado/)).toBeInTheDocument(),
    );
  });

  it('6.4c — shows processing state when messages are not yet terminal', async () => {
    server.use(
      http.get('http://localhost:8000/api/comunicaciones/lotes/:loteId', () =>
        HttpResponse.json({
          lote_id: 'lote-1',
          tenant_id: 't-1',
          total: 2,
          pendientes: 1,
          enviando: 1,
          enviados: 0,
          errores: 0,
          cancelados: 0,
        }),
      ),
    );
    render(makeTree('lote-1'));
    await waitFor(() =>
      expect(screen.getByText(/Procesando/)).toBeInTheDocument(),
    );
  });
});
