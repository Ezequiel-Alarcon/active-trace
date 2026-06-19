import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import WizardProgress from './WizardProgress';

const STEPS = ['Paso 1', 'Paso 2', 'Paso 3'] as const;

describe('WizardProgress', () => {
  it('8.13a — renders all steps', () => {
    render(<WizardProgress pasos={STEPS} pasoActual={0} />);
    expect(screen.getByText('Paso 1')).toBeInTheDocument();
    expect(screen.getByText('Paso 2')).toBeInTheDocument();
    expect(screen.getByText('Paso 3')).toBeInTheDocument();
  });

  it('8.13b — marks current step as active', () => {
    render(<WizardProgress pasos={STEPS} pasoActual={1} />);
    const step1 = screen.getByText('Paso 2');
    expect(step1.className).toContain('text-blue-700');
  });
});
