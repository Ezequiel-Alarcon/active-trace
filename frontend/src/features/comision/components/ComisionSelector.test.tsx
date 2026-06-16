import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ComisionSelector from './ComisionSelector';
import { STUB_COMISIONES } from '@/test/server';
import type { Comision } from '../types/comision';

const comisiones: Comision[] = STUB_COMISIONES;

describe('ComisionSelector', () => {
  it('2.2a — shows guide state when no comision is selected', () => {
    render(
      <ComisionSelector comisiones={comisiones} selected={null} onSelect={vi.fn()} />,
    );
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText(/Seleccioná una materia y cohorte/)).toBeInTheDocument();
  });

  it('2.2b — renders all comision options', () => {
    render(
      <ComisionSelector comisiones={comisiones} selected={null} onSelect={vi.fn()} />,
    );
    expect(screen.getByText('Matemáticas · 2024')).toBeInTheDocument();
  });

  it('2.2c — calls onSelect with the chosen comision id', async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(
      <ComisionSelector comisiones={comisiones} selected={null} onSelect={onSelect} />,
    );
    await user.selectOptions(screen.getByRole('combobox'), 'c-1');
    expect(onSelect).toHaveBeenCalledWith('c-1');
  });

  it('2.2d — hides guide state when comision is already selected', () => {
    render(
      <ComisionSelector comisiones={comisiones} selected="c-1" onSelect={vi.fn()} />,
    );
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
});
