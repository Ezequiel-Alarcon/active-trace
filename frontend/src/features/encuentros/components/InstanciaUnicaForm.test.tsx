import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse, server } from '@/test/server';
import InstanciaUnicaForm from './InstanciaUnicaForm';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <InstanciaUnicaForm />
    </QueryClientProvider>
  );
}

describe('InstanciaUnicaForm', () => {
  it('validates cohorte_id before submit', async () => {
    const user = userEvent.setup();
    render(makeTree());

    await waitFor(() => {
      expect(screen.getByRole('option', { name: /Álgebra/i })).toBeInTheDocument();
    });

    await user.selectOptions(screen.getByLabelText('Materia'), 'mat-1');
    await user.type(screen.getByLabelText('Título'), 'Encuentro especial');
    await user.type(screen.getByLabelText('Hora de inicio'), '18:00');
    await user.type(screen.getByLabelText('Hora de fin'), '20:00');
    await user.click(screen.getByRole('button', { name: 'Crear' }));

    expect(await screen.findByText('Este campo es obligatorio')).toBeInTheDocument();
  });

  it('submits with cohorte_id and shows backend 422 inline', async () => {
    const user = userEvent.setup();
    let capturedBody: Record<string, unknown> | null = null;

    server.use(
      http.post('http://localhost:8000/api/encuentros/instancias/unico', async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ id: 'inst-123' }, { status: 201 });
      }),
    );

    render(makeTree());

    await waitFor(() => {
      expect(screen.getByRole('option', { name: /Álgebra/i })).toBeInTheDocument();
    });

    await user.selectOptions(screen.getByLabelText('Materia'), 'mat-1');
    await user.selectOptions(screen.getByLabelText('Cohorte'), 'coh-1');
    await user.type(screen.getByLabelText('Título'), 'Encuentro especial');
    await user.type(screen.getByLabelText('Hora de inicio'), '18:00');
    await user.type(screen.getByLabelText('Hora de fin'), '20:00');
    await user.selectOptions(screen.getByLabelText('Modalidad'), 'video');
    await user.type(screen.getByLabelText('Enlace'), 'https://videos.trace.com/1');
    await user.click(screen.getByRole('button', { name: 'Crear' }));

    await waitFor(() => {
      expect(screen.getByText('Encuentro único creado correctamente.')).toBeInTheDocument();
    });

    expect(capturedBody?.cohorte_id).toBe('coh-1');

    server.use(
      http.post('http://localhost:8000/api/encuentros/instancias/unico', () =>
        HttpResponse.json(
          { detail: [{ loc: ['body', 'cohorte_id'], msg: 'Cohorte inválida' }] },
          { status: 422 },
        ),
      ),
    );

    await user.selectOptions(screen.getByLabelText('Materia'), 'mat-1');
    await user.selectOptions(screen.getByLabelText('Cohorte'), 'coh-1');
    await user.type(screen.getByLabelText('Título'), 'Encuentro 422');
    await user.type(screen.getByLabelText('Hora de inicio'), '10:00');
    await user.type(screen.getByLabelText('Hora de fin'), '11:00');
    await user.click(screen.getByRole('button', { name: 'Crear' }));

    expect(await screen.findByText('Cohorte inválida')).toBeInTheDocument();
  });
});
