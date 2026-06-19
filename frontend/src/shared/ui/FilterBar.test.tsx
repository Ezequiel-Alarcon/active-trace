import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import FilterBar from './FilterBar';

describe('FilterBar', () => {
  it('2.8 — renderiza los controles hijos', () => {
    render(
      <FilterBar>
        <input aria-label="Buscar" />
        <button>Aplicar</button>
      </FilterBar>,
    );
    expect(screen.getByLabelText('Buscar')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Aplicar' })).toBeInTheDocument();
  });

  it('2.8 — dispone los controles en fila flexible', () => {
    render(<FilterBar>{<span>f</span>}</FilterBar>);
    expect(screen.getByText('f').parentElement?.className).toContain('flex');
  });
});
