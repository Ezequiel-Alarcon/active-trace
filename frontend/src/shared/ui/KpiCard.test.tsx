import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import KpiCard from './KpiCard';

describe('KpiCard', () => {
  it('2.7 — muestra el valor y la etiqueta', () => {
    render(<KpiCard label="Atrasados" value={12} />);
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('Atrasados')).toBeInTheDocument();
  });

  it('2.7 — el valor se muestra destacado (texto grande)', () => {
    render(<KpiCard label="Aprobaciones" value={45} />);
    expect(screen.getByText('45').className).toContain('text-2xl');
  });
});
