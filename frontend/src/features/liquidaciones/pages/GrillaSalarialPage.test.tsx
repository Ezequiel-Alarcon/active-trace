import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import GrillaSalarialPage from './GrillaSalarialPage';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <GrillaSalarialPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('GrillaSalarialPage', () => {
  it('3.4a — shows tabs and switches to Plus', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await waitFor(() => expect(screen.getByText(/Grilla salarial/i)).toBeInTheDocument());
    expect(screen.getByText('Salario Base')).toBeInTheDocument();
    await user.click(screen.getByText('Plus'));
    await waitFor(() => expect(screen.getByText('PLUS-ACT')).toBeInTheDocument());
  });
});
