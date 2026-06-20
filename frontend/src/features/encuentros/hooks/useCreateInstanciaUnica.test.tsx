import { describe, it, expect } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse, server } from '@/test/server';
import { useCreateInstanciaUnica } from './useCreateInstanciaUnica';

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
  };
}

describe('useCreateInstanciaUnica', () => {
  it('creates an instance with cohorte_id and resolves successfully', async () => {
    let capturedBody: Record<string, unknown> | null = null;

    server.use(
      http.post('http://localhost:8000/api/encuentros/instancias/unico', async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ id: 'inst-123' }, { status: 201 });
      }),
    );

    const { result } = renderHook(() => useCreateInstanciaUnica(), { wrapper: makeWrapper() });

    await act(async () => {
      await result.current.mutateAsync({
        materia_id: 'mat-1',
        cohorte_id: 'coh-1',
        fecha: '2026-06-22',
        hora_inicio: '18:00',
        hora_fin: '20:00',
        titulo: 'Consulta',
        meet_url: null,
        video_url: 'https://videos.trace.com/demo',
        comentario: null,
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(capturedBody?.cohorte_id).toBe('coh-1');
  });

  it('surfaces backend validation errors', async () => {
    server.use(
      http.post('http://localhost:8000/api/encuentros/instancias/unico', () =>
        HttpResponse.json(
          { detail: [{ loc: ['body', 'cohorte_id'], msg: 'Field required' }] },
          { status: 422 },
        ),
      ),
    );

    const { result } = renderHook(() => useCreateInstanciaUnica(), { wrapper: makeWrapper() });

    await act(async () => {
      try {
        await result.current.mutateAsync({
          materia_id: 'mat-1',
          cohorte_id: '',
          fecha: '2026-06-22',
          hora_inicio: '18:00',
          hora_fin: '20:00',
          titulo: 'Consulta',
          meet_url: null,
          video_url: null,
          comentario: null,
        });
      } catch {
        // expected
      }
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
