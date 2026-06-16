import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { http, HttpResponse, server } from '@/test/server';
import { STUB_COMISIONES } from '@/test/server';
import { useComisionesDisponibles } from './useComisionesDisponibles';

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe('useComisionesDisponibles', () => {
  it('2.1a — returns list of comisiones from the session', async () => {
    server.use(
      http.get('http://localhost:8000/api/comisiones', () =>
        HttpResponse.json(STUB_COMISIONES),
      ),
    );
    const { result } = renderHook(() => useComisionesDisponibles(), {
      wrapper: makeWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data![0].materia_nombre).toBe('Matemáticas');
  });

  it('2.1b — returns empty list when no comisiones available', async () => {
    server.use(
      http.get('http://localhost:8000/api/comisiones', () =>
        HttpResponse.json([]),
      ),
    );
    const { result } = renderHook(() => useComisionesDisponibles(), {
      wrapper: makeWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(0);
  });
});
