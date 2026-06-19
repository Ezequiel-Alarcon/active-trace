import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import SetupPage from './SetupPage';

function makeTree() {
  const qc = new QueryClient();
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <SetupPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('SetupPage', () => {
  it('8.13c — renders initial wizard with progress bar', () => {
    render(makeTree());
    expect(screen.getByText('Setup de Cuatrimestre')).toBeInTheDocument();
    expect(screen.getAllByText('Crear cohorte').length).toBeGreaterThanOrEqual(1);
  });

  it('8.13d — navigates to step 2 on Siguiente', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await user.click(screen.getByText('Siguiente'));
    expect(screen.getAllByText('Clonar equipo').length).toBeGreaterThanOrEqual(1);
  });

  it('8.13e — shows summary after completing all steps', async () => {
    const user = userEvent.setup();
    render(makeTree());
    for (let i = 0; i < 7; i++) {
      const btn = screen.getByText(i < 6 ? 'Siguiente' : 'Finalizar');
      await user.click(btn);
    }
    expect(screen.getByText('Setup completado')).toBeInTheDocument();
    expect(screen.getByText('Resumen de operaciones realizadas')).toBeInTheDocument();
  });

  it('8.13f — Previous button navigates back', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await user.click(screen.getByText('Siguiente'));
    expect(screen.getAllByText('Clonar equipo').length).toBeGreaterThanOrEqual(1);
    await user.click(screen.getByText('Anterior'));
    expect(screen.getAllByText('Crear cohorte').length).toBeGreaterThanOrEqual(1);
  });
});
