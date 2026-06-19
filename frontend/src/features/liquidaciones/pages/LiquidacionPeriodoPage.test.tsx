import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import LiquidacionPeriodoPage from './LiquidacionPeriodoPage';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <LiquidacionPeriodoPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('LiquidacionPeriodoPage', () => {
  it('3.1a — renders page header and filter bar', async () => {
    render(makeTree());
    await waitFor(() => expect(screen.getByText(/Liquidaciones del período/i)).toBeInTheDocument());
    expect(screen.getByLabelText(/Cohorte/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Mes/i)).toBeInTheDocument();
  });

  it('3.1b — selecting cohorte and mes loads data', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await waitFor(() => expect(screen.getByText(/Licenciatura en Matemática/i)).toBeInTheDocument());
    await user.selectOptions(screen.getByLabelText(/Cohorte/i), 'car-1');
    await user.type(screen.getByLabelText(/Mes/i), '2024-06');
    await waitFor(() => expect(screen.getByText('Carlos López')).toBeInTheDocument());
  });
});
