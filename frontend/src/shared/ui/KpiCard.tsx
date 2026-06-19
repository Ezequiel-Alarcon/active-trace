import type { ReactNode } from 'react';
import Card from './Card';

interface KpiCardProps {
  label: string;
  value: ReactNode;
}

/** Métrica clave: número grande + etiqueta. */
export default function KpiCard({ label, value }: KpiCardProps) {
  return (
    <Card className="flex flex-col gap-1">
      <span className="text-2xl font-semibold text-gray-800">{value}</span>
      <span className="text-sm text-gray-500">{label}</span>
    </Card>
  );
}
