import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse, server } from '@/test/server';
import SlotFormWizard from './SlotFormWizard';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <SlotFormWizard />
    </QueryClientProvider>
  );
}

describe('SlotFormWizard', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });

  it('blocks step navigation when cohorte_id is missing', async () => {
    const user = userEvent.setup();
    render(makeTree());

    await waitFor(() => {
      expect(screen.getByRole('option', { name: /Álgebra/i })).toBeInTheDocument();
    });

    await user.selectOptions(screen.getByLabelText('Materia'), 'mat-1');
    await user.click(screen.getByRole('button', { name: 'Siguiente' }));

    expect(await screen.findByText('Este campo es obligatorio')).toBeInTheDocument();
    expect(screen.getByText('Paso 1 · Contexto académico')).toBeInTheDocument();
  });

  it('navigates through steps, persists state, and submits including cohorte_id', async () => {
    const user = userEvent.setup();
    let capturedBody: Record<string, unknown> | null = null;

    server.use(
      http.post('http://localhost:8000/api/encuentros/slots', async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ id: 'sl-123' }, { status: 201 });
      }),
    );

    render(makeTree());

    await waitFor(() => {
      expect(screen.getByRole('option', { name: /Álgebra/i })).toBeInTheDocument();
    });

    await user.selectOptions(screen.getByLabelText('Materia'), 'mat-1');
    await user.selectOptions(screen.getByLabelText('Cohorte'), 'coh-1');
    await user.click(screen.getByRole('button', { name: 'Siguiente' }));

    await user.selectOptions(screen.getByLabelText('Modalidad'), 'meet');
    await user.type(screen.getByLabelText('Hora de inicio'), '18:00');
    await user.type(screen.getByLabelText('Hora de fin'), '20:00');
    await user.type(screen.getByLabelText('Enlace'), 'https://meet.google.com/trace');
    await user.click(screen.getByRole('button', { name: 'Siguiente' }));

    await user.clear(screen.getByLabelText('Cantidad de semanas'));
    await user.type(screen.getByLabelText('Cantidad de semanas'), '2');
    await user.clear(screen.getByLabelText('Título'));
    await user.type(screen.getByLabelText('Título'), 'Teórica');
    await user.click(screen.getByRole('button', { name: 'Siguiente' }));

    expect(screen.getByText('Paso 4 · Preview')).toBeInTheDocument();
    expect(window.sessionStorage.getItem('encuentros-slot-wizard')).toContain('coh-1');

    await user.click(screen.getByRole('button', { name: 'Crear slot' }));

    await waitFor(() => {
      expect(screen.getByText('Slot creado correctamente.')).toBeInTheDocument();
    });

    expect(capturedBody?.cohorte_id).toBe('coh-1');
    expect(capturedBody?.meet_url).toBe('https://meet.google.com/trace');
  });
});
