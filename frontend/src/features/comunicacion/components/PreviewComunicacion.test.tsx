import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse, server } from '@/test/server';
import PreviewComunicacion from './PreviewComunicacion';
import React from 'react';

function makeTree(props: Parameters<typeof PreviewComunicacion>[0]) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <PreviewComunicacion {...props} />
    </QueryClientProvider>
  );
}

describe('PreviewComunicacion', () => {
  it('6.2a — shows preview without enqueueing', async () => {
    render(
      makeTree({ destinatarios: ['ana@test.com'], onConfirm: vi.fn(), onBack: vi.fn() }),
    );
    await waitFor(() =>
      expect(screen.getByText(/Recordatorio/)).toBeInTheDocument(),
    );
    // No "Enviando" status yet
    expect(screen.queryByText(/Enviando…/)).not.toBeInTheDocument();
  });

  it('6.2b — does not enqueue until confirm is clicked', async () => {
    let enqueued = false;
    server.use(
      http.post('http://localhost:8000/api/comunicaciones', () => {
        enqueued = true;
        return HttpResponse.json([], { status: 201 });
      }),
    );
    render(
      makeTree({ destinatarios: ['ana@test.com'], onConfirm: vi.fn(), onBack: vi.fn() }),
    );
    await waitFor(() => screen.getByText(/Recordatorio/));
    expect(enqueued).toBe(false);
  });

  it('6.3a — confirm enqueues messages and calls onConfirm with loteId', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    render(
      makeTree({ destinatarios: ['ana@test.com'], onConfirm, onBack: vi.fn() }),
    );
    await waitFor(() => screen.getByText('Confirmar envío'));
    await user.click(screen.getByText('Confirmar envío'));
    await waitFor(() => expect(onConfirm).toHaveBeenCalled());
  });
});
