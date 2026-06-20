import type { ReactNode } from 'react';
import Card from './Card';

interface KpiCardProps {
  label: string;
  value: ReactNode;
}

/** Métrica clave: número grande con trazo izquierdo + etiqueta. */
export default function KpiCard({ label, value }: KpiCardProps) {
  return (
    <Card className="flex flex-col gap-1 border-l-4 border-l-blue-500 pl-4">
      <span className="text-3xl font-semibold text-slate-900 tabular-nums">{value}</span>
      <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</span>
    </Card>
  );
}
