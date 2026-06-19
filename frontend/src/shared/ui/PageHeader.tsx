import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  /** Acciones alineadas a la derecha (botones, enlaces). */
  actions?: ReactNode;
}

/** Encabezado de página: título a la izquierda, acciones a la derecha. */
export default function PageHeader({ title, actions }: PageHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-4">
      <h1 className="text-2xl font-semibold text-gray-800">{title}</h1>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
