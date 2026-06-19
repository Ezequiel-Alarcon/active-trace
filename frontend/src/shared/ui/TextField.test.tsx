import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { useRef, useEffect } from 'react';
import TextField from './TextField';

describe('TextField', () => {
  it('2.11 — asocia el label con el input vía id', () => {
    render(<TextField id="email" label="Email" />);
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
  });

  it('2.11 — muestra el mensaje de error cuando se pasa', () => {
    render(<TextField id="email" label="Email" error="Email inválido" />);
    expect(screen.getByText('Email inválido')).toBeInTheDocument();
  });

  it('2.11 — sin error no renderiza mensaje', () => {
    render(<TextField id="x" label="X" />);
    expect(screen.queryByText(/inválido/)).not.toBeInTheDocument();
  });

  it('2.11 — reenvía props nativas (type, defaultValue) al input', () => {
    render(<TextField id="pwd" label="Pass" type="password" defaultValue="abc" />);
    const input = screen.getByLabelText('Pass') as HTMLInputElement;
    expect(input.type).toBe('password');
    expect(input.value).toBe('abc');
  });

  it('2.11 — forwardRef apunta al input (compatible con react-hook-form)', () => {
    function Probe() {
      const ref = useRef<HTMLInputElement>(null);
      useEffect(() => {
        if (ref.current) ref.current.dataset.touched = 'yes';
      }, []);
      return <TextField id="r" label="R" ref={ref} />;
    }
    render(<Probe />);
    expect((screen.getByLabelText('R') as HTMLInputElement).dataset.touched).toBe('yes');
  });
});
