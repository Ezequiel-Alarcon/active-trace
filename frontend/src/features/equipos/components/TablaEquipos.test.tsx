import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import TablaEquipos from './TablaEquipos';
import type { AsignacionResponse } from '../types/equipos';

const MOCK_EQUIPOS: AsignacionResponse[] = [
  {
    id: 'eq-1', materia_id: 'm-1', materia_nombre: 'Matemáticas',
    carrera: 'Lic. Matemática', cohorte: '2024', comisiones: ['Com A'],
    rol: 'TITULAR', docente_id: 'u-1', docente_nombre: 'Carlos López',
    vigencia_desde: '2024-03-01', vigencia_hasta: '', estado: 'activo',
  },
  {
    id: 'eq-2', materia_id: 'm-2', materia_nombre: 'Física',
    carrera: 'Lic. Física', cohorte: '2024', comisiones: ['Com B'],
    rol: 'ADJUNTO', docente_id: 'u-2', docente_nombre: 'María Pérez',
    vigencia_desde: '2024-03-01', vigencia_hasta: '2024-12-31', estado: 'activo',
  },
];

function makeTree(equipos: AsignacionResponse[] = MOCK_EQUIPOS) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <TablaEquipos equipos={equipos} />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('TablaEquipos', () => {
  it('2.11a — renders equipo rows from API', () => {
    render(makeTree());
    expect(screen.getByText('Carlos López')).toBeInTheDocument();
    expect(screen.getByText('Matemáticas')).toBeInTheDocument();
    expect(screen.getByText('María Pérez')).toBeInTheDocument();
  });

  it('2.11b — shows empty state when no equipos', () => {
    render(makeTree([]));
    expect(screen.getByText('No hay asignaciones docentes registradas.')).toBeInTheDocument();
  });
});
