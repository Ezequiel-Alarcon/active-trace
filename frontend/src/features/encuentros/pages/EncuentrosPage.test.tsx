import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse, server } from '@/test/server';
import EncuentrosPage from './EncuentrosPage';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <EncuentrosPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('EncuentrosPage', () => {
  it('6.8a — shows tabs with Encuentros content', async () => {
    render(makeTree());
    await waitFor(() => {
      expect(screen.getAllByText('Encuentros').length).toBeGreaterThanOrEqual(1);
    });
    expect(screen.getByText('Slots')).toBeInTheDocument();
    expect(screen.getByText('Guardias')).toBeInTheDocument();
  });

  it('6.8b — shows encuentros table by default', async () => {
    render(makeTree());
    await waitFor(() => {
      expect(screen.getByText('Matemáticas')).toBeInTheDocument();
      expect(screen.getByText('Pendiente')).toBeInTheDocument();
    });
  });

  it('6.8c — switches to Guardias tab and shows guardias', async () => {
    const user = userEvent.setup();
    render(makeTree());
    await waitFor(() => screen.getByText('Guardias'));
    await user.click(screen.getByText('Guardias'));
    await waitFor(() => {
      expect(screen.getByText('Carlos López')).toBeInTheDocument();
    });
  });
});
