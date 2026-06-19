import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import StatusBadge from './StatusBadge';

describe('StatusBadge', () => {
  it('2.3 — atrasado aplica rojo', () => {
    render(<StatusBadge estado="atrasado">Atrasado</StatusBadge>);
    const el = screen.getByText('Atrasado');
    expect(el.className).toContain('bg-red-100');
    expect(el.className).toContain('text-red-700');
  });

  it('2.3 — en-envio aplica azul (estado de cola)', () => {
    render(<StatusBadge estado="en-envio">En envío</StatusBadge>);
    expect(screen.getByText('En envío').className).toContain('bg-blue-100');
  });

  it('2.3 — enviado aplica verde', () => {
    render(<StatusBadge estado="enviado">Enviado</StatusBadge>);
    expect(screen.getByText('Enviado').className).toContain('bg-green-100');
  });

  it('2.3 — pendiente-cola aplica gris (distinto de pendiente/ámbar)', () => {
    render(
      <>
        <StatusBadge estado="pendiente-cola">Pendiente</StatusBadge>
        <StatusBadge estado="pendiente">Sin corregir</StatusBadge>
      </>,
    );
    expect(screen.getByText('Pendiente').className).toContain('bg-gray-100');
    expect(screen.getByText('Sin corregir').className).toContain('bg-amber-100');
  });
});
