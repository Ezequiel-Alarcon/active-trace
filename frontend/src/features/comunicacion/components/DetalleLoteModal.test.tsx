import { describe, it, expect } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { http, HttpResponse, server } from '@/test/server';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import DetalleLoteModal from './DetalleLoteModal';
import type { LotePendienteResponse } from '../types/comunicacion';

const LOTE_MOCK: LotePendienteResponse = {
  lote_id: 'lote-1',
  tenant_id: 't-1',
  total: 3,
  pendientes: 3,
  enviando: 0,
  enviados: 0,
  errores: 0,
  cancelados: 0,
  asunto: 'Recordatorio de evaluación',
  cuerpo: 'Te informamos que tienes evaluaciones pendientes.',
  solicitado_por_nombre: 'Carlos López',
  destinatarios: ['ana@test.com', 'pedro@test.com', 'juan@test.com'],
  created_at: '2024-01-01T10:00:00Z',
};

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={qc}>
        {children}
      </QueryClientProvider>
    );
  };
}

describe('DetalleLoteModal', () => {
  it('renders lote details correctly', () => {
    render(<DetalleLoteModal lote={LOTE_MOCK} onClose={vi.fn()} />, { wrapper: makeWrapper() });
    expect(screen.getByText('Recordatorio de evaluación')).toBeInTheDocument();
    expect(screen.getByText('Carlos López')).toBeInTheDocument();
    expect(screen.getByText('3 mensajes')).toBeInTheDocument();
    expect(screen.getByText('ana@test.com')).toBeInTheDocument();
  });

  it('shows truncated cuerpo when exceeds 500 chars', () => {
    const longCuerpo = 'A'.repeat(600);
    const lote: LotePendienteResponse = { ...LOTE_MOCK, cuerpo: longCuerpo };
    render(<DetalleLoteModal lote={lote} onClose={vi.fn()} />, { wrapper: makeWrapper() });
    expect(screen.getByText('A'.repeat(500) + '…')).toBeInTheDocument();
  });

  it('shows "… y N más" when destinatarios exceed 20', () => {
    const manyDestinatarios = Array.from({ length: 25 }, (_, i) => `user${i}@test.com`);
    const lote: LotePendienteResponse = { ...LOTE_MOCK, destinatarios: manyDestinatarios };
    render(<DetalleLoteModal lote={lote} onClose={vi.fn()} />, { wrapper: makeWrapper() });
    expect(screen.getByText('… y 5 más')).toBeInTheDocument();
  });

  it('opens confirmation dialog on Approbar click', () => {
    render(<DetalleLoteModal lote={LOTE_MOCK} onClose={vi.fn()} />, { wrapper: makeWrapper() });
    fireEvent.click(screen.getByText('Aprobar'));
    expect(screen.getByText(/^¿Aprobar este envío\?/)).toBeInTheDocument();
    expect(screen.getByText(/Se procederá a enviar 3 mensajes/)).toBeInTheDocument();
  });

  it('opens confirmation dialog on Rechazar click', () => {
    render(<DetalleLoteModal lote={LOTE_MOCK} onClose={vi.fn()} />, { wrapper: makeWrapper() });
    fireEvent.click(screen.getByText('Rechazar'));
    expect(screen.getByText(/^¿Rechazar este envío\?/)).toBeInTheDocument();
    expect(screen.getByText(/Esta acción cancelará 3 mensajes/)).toBeInTheDocument();
  });

  it('closes confirmation on Cancelar in dialog', () => {
    render(<DetalleLoteModal lote={LOTE_MOCK} onClose={vi.fn()} />, { wrapper: makeWrapper() });
    fireEvent.click(screen.getByText('Aprobar'));
    expect(screen.getByText(/^¿Aprobar este envío\?/)).toBeInTheDocument();
    fireEvent.click(screen.getByText('Cancelar'));
    expect(screen.queryByText(/^¿Aprobar este envío\?/)).not.toBeInTheDocument();
    expect(screen.getByText('Recordatorio de evaluación')).toBeInTheDocument();
  });

  it('calls onClose after successful approve', async () => {
    const onClose = vi.fn();
    render(<DetalleLoteModal lote={LOTE_MOCK} onClose={onClose} />, { wrapper: makeWrapper() });
    fireEvent.click(screen.getByText('Aprobar'));
    fireEvent.click(screen.getByText('Confirmar'));
    await waitFor(() => expect(onClose).toHaveBeenCalled());
  });

  it('shows error toast when approve fails', async () => {
    server.use(
      http.post('http://localhost:8000/api/comunicaciones/lotes/:loteId/aprobar', () =>
        HttpResponse.json({}, { status: 500 }),
      ),
    );
    render(<DetalleLoteModal lote={LOTE_MOCK} onClose={vi.fn()} />, { wrapper: makeWrapper() });
    fireEvent.click(screen.getByText('Aprobar'));
    fireEvent.click(screen.getByText('Confirmar'));
    await waitFor(() => expect(screen.getByText('Error al aprobar el lote')).toBeInTheDocument());
  });

  it('shows error toast when reject fails', async () => {
    server.use(
      http.post('http://localhost:8000/api/comunicaciones/lotes/:loteId/rechazar', () =>
        HttpResponse.json({}, { status: 500 }),
      ),
    );
    render(<DetalleLoteModal lote={LOTE_MOCK} onClose={vi.fn()} />, { wrapper: makeWrapper() });
    fireEvent.click(screen.getByText('Rechazar'));
    fireEvent.click(screen.getByText('Confirmar'));
    await waitFor(() => expect(screen.getByText('Error al rechazar el lote')).toBeInTheDocument());
  });
});
