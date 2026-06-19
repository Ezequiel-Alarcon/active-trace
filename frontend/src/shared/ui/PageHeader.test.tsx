import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import PageHeader from './PageHeader';

describe('PageHeader', () => {
  it('2.5 — muestra el título como heading', () => {
    render(<PageHeader title="Notas finales" />);
    expect(screen.getByRole('heading', { name: 'Notas finales' })).toBeInTheDocument();
  });

  it('2.5 — renderiza las acciones', () => {
    render(<PageHeader title="Reportes" actions={<button>Exportar</button>} />);
    expect(screen.getByRole('button', { name: 'Exportar' })).toBeInTheDocument();
  });
});
