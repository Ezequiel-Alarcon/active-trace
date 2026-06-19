import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import AuditoriaPanelPage from './AuditoriaPanelPage';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <AuditoriaPanelPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('AuditoriaPanelPage', () => {
  it('4.3a — renders panel header and metadata cards', async () => {
    render(makeTree());
    await waitFor(() => expect(screen.getByText(/Panel de auditoría/i)).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText('200')).toBeInTheDocument());
  });
});
