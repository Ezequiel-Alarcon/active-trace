import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import AuditoriaLogPage from './AuditoriaLogPage';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <AuditoriaLogPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('AuditoriaLogPage', () => {
  it('4.4a — renders page and shows log entries', async () => {
    render(makeTree());
    await waitFor(() => expect(screen.getByText(/Log de auditoría/i)).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText(/admin@trace.com/i)).toBeInTheDocument());
  });
});
