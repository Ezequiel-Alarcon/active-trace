import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Badge from './Badge';

describe('Badge', () => {
  it('2.2 — renderiza su contenido', () => {
    render(<Badge>Nuevo</Badge>);
    expect(screen.getByText('Nuevo')).toBeInTheDocument();
  });

  it('2.2 — es un pill redondeado', () => {
    render(<Badge>X</Badge>);
    expect(screen.getByText('X').className).toContain('rounded');
  });

  it('2.2 — admite clases extra sin perder las base', () => {
    render(<Badge className="bg-green-100">OK</Badge>);
    const el = screen.getByText('OK');
    expect(el.className).toContain('rounded');
    expect(el.className).toContain('bg-green-100');
  });
});
