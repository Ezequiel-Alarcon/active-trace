import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import FacturasPage from './FacturasPage';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <FacturasPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('FacturasPage', () => {
  it('5.1a — renders header and shows facturas', async () => {
    render(makeTree());
    await waitFor(() => expect(screen.getByText(/Facturas/i)).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText(/Factura junio 2024/i)).toBeInTheDocument());
    expect(screen.getByText(/María Pérez/i)).toBeInTheDocument();
  });

  it('5.1b — opens registrar modal on button click', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await waitFor(() => expect(screen.getByText(/Facturas/i)).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: 'Registrar factura' }));
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Registrar factura' })).toBeInTheDocument());
  });
});
