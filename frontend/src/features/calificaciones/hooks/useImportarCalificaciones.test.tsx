import { describe, it, expect } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { http, HttpResponse, server } from '@/test/server';
import { usePreviewImport, useConfirmImport } from './useImportarCalificaciones';

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

const FAKE_FILE = new File(['email,nota\nana@test.com,8'], 'notas.csv', { type: 'text/csv' });

describe('usePreviewImport', () => {
  it('3.2a — happy path: returns preview data', async () => {
    const { result } = renderHook(() => usePreviewImport(), { wrapper: makeWrapper() });
    await act(async () => {
      result.current.mutate({ file: FAKE_FILE });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.preview_token).toBe('tok-abc');
    expect(result.current.data?.rows).toHaveLength(1);
  });

  it('3.2b — error path: exposes backend error message', async () => {
    server.use(
      http.post('http://localhost:8000/api/calificaciones/import/preview', () =>
        HttpResponse.json({ detail: 'Formato inválido' }, { status: 400 }),
      ),
    );
    const { result } = renderHook(() => usePreviewImport(), { wrapper: makeWrapper() });
    await act(async () => {
      result.current.mutate({ file: FAKE_FILE });
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeTruthy();
  });
});

describe('useConfirmImport', () => {
  it('3.2c — happy path: returns persisted/skipped/failed counts', async () => {
    const { result } = renderHook(() => useConfirmImport(), { wrapper: makeWrapper() });
    await act(async () => {
      result.current.mutate('tok-abc');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.persisted).toBe(1);
    expect(result.current.data?.skipped).toBe(0);
    expect(result.current.data?.failed).toBe(0);
  });
});
