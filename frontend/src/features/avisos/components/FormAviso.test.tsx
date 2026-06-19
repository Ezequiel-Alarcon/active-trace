import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import FormAviso from './FormAviso';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <FormAviso />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('FormAviso', () => {
  it('3.8a — renders all form fields', () => {
    render(makeTree());
    expect(screen.getByLabelText('Título')).toBeInTheDocument();
    expect(screen.getByLabelText('Cuerpo')).toBeInTheDocument();
    expect(screen.getByLabelText('Alcance')).toBeInTheDocument();
    expect(screen.getByLabelText('Severidad')).toBeInTheDocument();
    expect(screen.getByLabelText('Vigencia desde')).toBeInTheDocument();
    expect(screen.getByLabelText('Vigencia hasta')).toBeInTheDocument();
    expect(screen.getByLabelText('Requiere confirmación de lectura')).toBeInTheDocument();
  });

  it('3.8b — shows validation error when titulo is empty', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await user.click(screen.getByText('Publicar aviso'));
    await waitFor(() =>
      expect(screen.getByText(/El título es obligatorio/)).toBeInTheDocument(),
    );
  });

  it('3.8c — shows contexto field when alcance is not Global', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await user.selectOptions(screen.getByLabelText('Alcance'), 'PorMateria');
    await waitFor(() =>
      expect(screen.getByText(/ID Materia/)).toBeInTheDocument(),
    );
  });

  it('3.8d — editing mode shows update button', () => {
    const aviso = {
      id: 'av-1', titulo: 'Test', cuerpo: 'Cuerpo', alcance: 'Global' as const,
      contexto_id: undefined, roles_destinatarios: [], severidad: 'Informativo' as const,
      vigencia_desde: '2024-01-01', vigencia_hasta: '2024-12-31', orden_prioridad: 1,
      estado: 'activo' as const, requiere_ack: false, created_at: '', updated_at: '',
    };
    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter>
          <FormAviso aviso={aviso} />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(screen.getByText('Actualizar aviso')).toBeInTheDocument();
  });
});
