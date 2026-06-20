import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  /** Acciones alineadas a la derecha (botones, enlaces). */
  actions?: ReactNode;
}

/** Encabezado de página: título con trazo izquierdo, acciones a la derecha. */
export default function PageHeader({ title, actions }: PageHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-6">
      <h1 className="text-2xl font-semibold text-slate-900 border-l-4 border-blue-500 pl-3 leading-tight">
        {title}
      </h1>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
