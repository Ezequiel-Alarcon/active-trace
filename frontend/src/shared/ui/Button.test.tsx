import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Button from './Button';

describe('Button', () => {
  it('2.1 — variante primary aplica azul blue-600', () => {
    render(<Button variant="primary">Guardar</Button>);
    expect(screen.getByRole('button', { name: 'Guardar' }).className).toContain('bg-blue-600');
  });

  it('2.1 — variante danger aplica rojo', () => {
    render(<Button variant="danger">Borrar</Button>);
    expect(screen.getByRole('button', { name: 'Borrar' }).className).toContain('bg-red-600');
  });

  it('2.1 — variante secondary NO usa el azul primario', () => {
    render(<Button variant="secondary">Cancelar</Button>);
    expect(screen.getByRole('button', { name: 'Cancelar' }).className).not.toContain('bg-blue-600');
  });

  it('2.1 — disabled ignora clics', async () => {
    const onClick = vi.fn();
    render(<Button disabled onClick={onClick}>X</Button>);
    await userEvent.click(screen.getByRole('button', { name: 'X' }));
    expect(onClick).not.toHaveBeenCalled();
  });

  it('2.1 — habilitado dispara onClick', async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Ok</Button>);
    await userEvent.click(screen.getByRole('button', { name: 'Ok' }));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
