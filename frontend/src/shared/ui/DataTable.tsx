import type { ReactNode } from 'react';
import EmptyState from './EmptyState';

export interface Column<T> {
  header: string;
  render: (row: T) => ReactNode;
  /** Clases extra para las celdas de esta columna. */
  className?: string;
}

interface Selection<T> {
  selectedKeys: Set<string>;
  onToggle: (key: string) => void;
  ariaLabel: (row: T) => string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T, index: number) => string;
  /** Mensaje del estado vacío cuando no hay filas. */
  emptyMessage?: ReactNode;
  /** Habilita la columna de selección por checkbox. */
  selection?: Selection<T>;
}

/**
 * Tabla genérica tipada. Render-prop por columna, selección opcional por checkbox
 * y estado vacío delegado a `EmptyState` cuando no hay filas.
 */
export default function DataTable<T>({
  columns,
  rows,
  rowKey,
  emptyMessage = 'No hay datos para mostrar.',
  selection,
}: DataTableProps<T>) {
  if (rows.length === 0) {
    return <EmptyState>{emptyMessage}</EmptyState>;
  }

  return (
    <table className="w-full text-sm border-collapse">
      <thead>
        <tr className="border-b border-gray-200">
          {selection && <th className="py-2 pr-3 text-left w-8" />}
          {columns.map((col) => (
            <th key={col.header} className="py-2 text-left font-medium text-gray-700">
              {col.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, index) => {
          const key = rowKey(row, index);
          return (
            <tr key={key} className="border-b border-gray-100 hover:bg-gray-50">
              {selection && (
                <td className="py-2 pr-3">
                  <input
                    type="checkbox"
                    aria-label={selection.ariaLabel(row)}
                    checked={selection.selectedKeys.has(key)}
                    onChange={() => selection.onToggle(key)}
                  />
                </td>
              )}
              {columns.map((col) => (
                <td key={col.header} className={`py-2 ${col.className ?? ''}`.trim()}>
                  {col.render(row)}
                </td>
              ))}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
