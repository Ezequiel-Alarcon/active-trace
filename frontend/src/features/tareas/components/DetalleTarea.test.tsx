import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import DetalleTarea from './DetalleTarea';
import type { TareaResponse } from '../types/tareas';

const MOCK_TAREA: TareaResponse = {
  id: 'tr-1',
  titulo: 'Revisar planificaciones',
  descripcion: 'Revisar planificaciones del cuatrimestre',
  materia_id: 'm-1',
  materia_nombre: 'Matemáticas',
  docente_asignado_id: 'u-1',
  docente_asignado_nombre: 'Carlos López',
  docente_asignador_id: 'usr-1',
  docente_asignador_nombre: 'Admin',
  estado: 'Pendiente',
  created_at: '2024-03-01T00:00:00Z',
  updated_at: '2024-03-01T00:00:00Z',
};

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <DetalleTarea tarea={MOCK_TAREA} onClose={() => {}} />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('DetalleTarea', () => {
  it('4.9a — shows tarea details and comments', async () => {
    render(makeTree());
    await waitFor(() => {
      expect(screen.getByText('Revisar planificaciones')).toBeInTheDocument();
    });
    expect(screen.getByText('Carlos López')).toBeInTheDocument();
    expect(screen.getByText(/Admin/)).toBeInTheDocument();
  });

  it('4.9b — adding a comment calls API', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await waitFor(() => screen.getByPlaceholderText('Nuevo comentario…'));
    const input = screen.getByPlaceholderText('Nuevo comentario…');
    await user.type(input, 'Nuevo comentario');
    await user.click(screen.getByText('Enviar'));
    await waitFor(() =>
      expect(screen.queryByText('Error al enviar comentario')).not.toBeInTheDocument(),
    );
  });
});
