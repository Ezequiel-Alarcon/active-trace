import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse, server } from '@/test/server';
import RankingVista from './RankingVista';
import React from 'react';

function makeTree() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <RankingVista comisionId="c-1" />
    </QueryClientProvider>
  );
}

describe('RankingVista', () => {
  it('4.2a — renders ranking table with data when materia_id provided', async () => {
    server.use(
      http.get('http://localhost:8000/api/analisis/ranking', () =>
        HttpResponse.json({
          materia_id: 'm-1',
          materia_nombre: 'Matemáticas',
          rankings: [
            { posicion: 1, usuario_id: 'u-1', nombre: 'Pedro', email: 'pedro@test.com', cantidad_aprobadas: 5, cantidad_totales: 6, nota_promedio: 8.5 },
            { posicion: 2, usuario_id: 'u-2', nombre: 'Laura', email: 'laura@test.com', cantidad_aprobadas: 3, cantidad_totales: 6, nota_promedio: 7.0 },
          ],
        }),
      ),
    );
    render(makeTree());
    await waitFor(() => expect(screen.getByText('Pedro')).toBeInTheDocument());
    // Ordered: Pedro before Laura
    const rows = screen.getAllByRole('row').slice(1); // skip header
    expect(rows[0]).toHaveTextContent('Pedro');
    expect(rows[1]).toHaveTextContent('Laura');
  });

  it('4.2b — filters out alumnos with zero aprobadas', async () => {
    server.use(
      http.get('http://localhost:8000/api/analisis/ranking', () =>
        HttpResponse.json({
          materia_id: 'm-1',
          materia_nombre: 'Matemáticas',
          rankings: [
            { posicion: 1, usuario_id: 'u-1', nombre: 'Pedro', email: 'pedro@test.com', cantidad_aprobadas: 3, cantidad_totales: 6, nota_promedio: 7.0 },
            { posicion: 2, usuario_id: 'u-2', nombre: 'Sin notas', email: 'zero@test.com', cantidad_aprobadas: 0, cantidad_totales: 6, nota_promedio: null },
          ],
        }),
      ),
    );
    render(makeTree());
    await waitFor(() => expect(screen.getByText('Pedro')).toBeInTheDocument());
    expect(screen.queryByText('Sin notas')).not.toBeInTheDocument();
  });
});
