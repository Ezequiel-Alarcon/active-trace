import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse, server } from '@/test/server';
import MonitorGeneralPage from './MonitorGeneralPage';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <MonitorGeneralPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('MonitorGeneralPage', () => {
  it('5.7a — shows monitor table with data', async () => {
    render(makeTree());
    await waitFor(() => expect(screen.getByText('Pedro')).toBeInTheDocument());
  });

  it('5.7b — empty state when no data', async () => {
    server.use(
      http.get('http://localhost:8000/api/monitores/general', () =>
        HttpResponse.json({ datos: [] }),
      ),
    );
    render(makeTree());
    await waitFor(() =>
      expect(screen.getByRole('status')).toBeInTheDocument(),
    );
  });
});
