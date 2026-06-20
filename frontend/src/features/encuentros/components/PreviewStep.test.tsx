import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import PreviewStep, { buildPreviewRows } from './PreviewStep';

const values = {
  materia_id: 'mat-1',
  cohorte_id: 'coh-1',
  titulo: 'Teórica semanal',
  dia_semana: 0,
  hora_inicio: '18:00',
  hora_fin: '20:00',
  fecha_inicio: '2026-06-22',
  cant_semanas: 3,
  modalidad: 'presencial' as const,
  link: '',
};

describe('PreviewStep', () => {
  it('calculates preview dates client-side for N weeks', () => {
    expect(buildPreviewRows(values)).toEqual([
      { fecha: '2026-06-22', hora_inicio: '18:00', hora_fin: '20:00', titulo: 'Teórica semanal' },
      { fecha: '2026-06-29', hora_inicio: '18:00', hora_fin: '20:00', titulo: 'Teórica semanal' },
      { fecha: '2026-07-06', hora_inicio: '18:00', hora_fin: '20:00', titulo: 'Teórica semanal' },
    ]);
  });

  it('renders the generated preview rows', () => {
    render(<PreviewStep values={values} />);

    expect(screen.getByText('2026-06-22')).toBeInTheDocument();
    expect(screen.getByText('2026-06-29')).toBeInTheDocument();
    expect(screen.getByText('2026-07-06')).toBeInTheDocument();
  });
});
