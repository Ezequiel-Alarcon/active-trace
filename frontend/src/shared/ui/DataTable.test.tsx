import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DataTable, { type Column } from './DataTable';

interface Fila {
  id: string;
  nombre: string;
}

const filas: Fila[] = [
  { id: '1', nombre: 'Ana' },
  { id: '2', nombre: 'Beto' },
];

const columns: Column<Fila>[] = [
  { header: 'Nombre', render: (r) => r.nombre },
];

describe('DataTable', () => {
  it('2.9 — con datos renderiza encabezados y una fila por elemento', () => {
    render(<DataTable rows={filas} columns={columns} rowKey={(r) => r.id} />);
    expect(screen.getByText('Nombre')).toBeInTheDocument();
    expect(screen.getByText('Ana')).toBeInTheDocument();
    expect(screen.getByText('Beto')).toBeInTheDocument();
    // 2 filas de cuerpo (las filas <tr> del tbody)
    expect(screen.getAllByRole('row')).toHaveLength(3); // 1 header + 2 datos
  });

  it('2.9 — sin datos muestra EmptyState en lugar del cuerpo', () => {
    render(
      <DataTable
        rows={[]}
        columns={columns}
        rowKey={(r) => r.id}
        emptyMessage="No hay datos."
      />,
    );
    expect(screen.getByRole('status')).toHaveTextContent('No hay datos.');
    expect(screen.queryByText('Ana')).not.toBeInTheDocument();
  });

  it('2.9 — con selección, clic en checkbox llama onToggle con la key', async () => {
    const onToggle = vi.fn();
    render(
      <DataTable
        rows={filas}
        columns={columns}
        rowKey={(r) => r.id}
        selection={{
          selectedKeys: new Set(),
          onToggle,
          ariaLabel: (r) => `Seleccionar ${r.nombre}`,
        }}
      />,
    );
    await userEvent.click(screen.getByLabelText('Seleccionar Ana'));
    expect(onToggle).toHaveBeenCalledWith('1');
  });

  it('2.9 — rowKey recibe el índice de fila (clave estable con ids duplicados/nulos)', () => {
    const dup: Fila[] = [
      { id: 'x', nombre: 'A' },
      { id: 'x', nombre: 'B' },
    ];
    const keys: string[] = [];
    render(
      <DataTable
        rows={dup}
        columns={columns}
        rowKey={(r, i) => {
          const k = `${r.id}-${i}`;
          keys.push(k);
          return k;
        }}
      />,
    );
    expect(keys).toEqual(['x-0', 'x-1']);
  });

  it('2.9 — con selección, refleja las keys ya seleccionadas como checked', () => {
    render(
      <DataTable
        rows={filas}
        columns={columns}
        rowKey={(r) => r.id}
        selection={{
          selectedKeys: new Set(['2']),
          onToggle: vi.fn(),
          ariaLabel: (r) => `Seleccionar ${r.nombre}`,
        }}
      />,
    );
    expect(screen.getByLabelText('Seleccionar Beto')).toBeChecked();
    expect(screen.getByLabelText('Seleccionar Ana')).not.toBeChecked();
  });
});
