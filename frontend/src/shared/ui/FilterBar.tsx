import type { ReactNode } from 'react';

interface FilterBarProps {
  children: ReactNode;
}

/** Barra de filtros horizontal: dispone los controles en fila flexible. */
export default function FilterBar({ children }: FilterBarProps) {
  return <div className="flex flex-wrap items-end gap-3 mb-4">{children}</div>;
}
