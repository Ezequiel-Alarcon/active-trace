import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import EmptyState from './EmptyState';

describe('EmptyState', () => {
  it('2.6 — muestra el mensaje con role status', () => {
    render(<EmptyState>No hay datos importados.</EmptyState>);
    const el = screen.getByRole('status');
    expect(el).toHaveTextContent('No hay datos importados.');
  });

  it('2.6 — usa contenedor gris', () => {
    render(<EmptyState>vacío</EmptyState>);
    expect(screen.getByRole('status').className).toContain('bg-gray-50');
  });
});
