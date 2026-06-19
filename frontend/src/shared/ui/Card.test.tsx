import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Card from './Card';

describe('Card', () => {
  it('2.4 — renderiza su contenido', () => {
    render(<Card>Contenido</Card>);
    expect(screen.getByText('Contenido')).toBeInTheDocument();
  });

  it('2.4 — tiene borde y esquinas redondeadas', () => {
    render(<Card>X</Card>);
    const el = screen.getByText('X');
    expect(el.className).toContain('border');
    expect(el.className).toContain('rounded');
  });
});
