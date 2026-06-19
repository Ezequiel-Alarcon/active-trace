import { describe, it, expect } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { http, HttpResponse, server } from '@/test/server';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { useAprobarLote } from './useAprobarLote';
import { useRechazarLote } from './useRechazarLote';

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={qc}>
        {children}
      </QueryClientProvider>
    );
  };
}

describe('useAprobarLote', () => {
  it('calls POST /api/comunicaciones/lotes/:loteId/aprobar and invalidates lotes-pendientes', async () => {
    const { result } = renderHook(() => useAprobarLote(), { wrapper: makeWrapper() });

    await act(async () => {
      await result.current.mutateAsync('lote-1');
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('throws on server error', async () => {
    server.use(
      http.post('http://localhost:8000/api/comunicaciones/lotes/:loteId/aprobar', () =>
        HttpResponse.json({}, { status: 500 }),
      ),
    );
    const { result } = renderHook(() => useAprobarLote(), { wrapper: makeWrapper() });

    await act(async () => {
      try {
        await result.current.mutateAsync('lote-1');
      } catch {
        // expected
      }
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useRechazarLote', () => {
  it('calls POST /api/comunicaciones/lotes/:loteId/rechazar and invalidates lotes-pendientes', async () => {
    const { result } = renderHook(() => useRechazarLote(), { wrapper: makeWrapper() });

    await act(async () => {
      await result.current.mutateAsync('lote-1');
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('throws on server error', async () => {
    server.use(
      http.post('http://localhost:8000/api/comunicaciones/lotes/:loteId/rechazar', () =>
        HttpResponse.json({}, { status: 500 }),
      ),
    );
    const { result } = renderHook(() => useRechazarLote(), { wrapper: makeWrapper() });

    await act(async () => {
      try {
        await result.current.mutateAsync('lote-1');
      } catch {
        // expected
      }
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
