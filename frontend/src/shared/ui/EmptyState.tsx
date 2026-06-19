import type { ReactNode } from 'react';

interface EmptyStateProps {
  children: ReactNode;
}

/** Estado vacío informativo (gris). Anuncia con role="status". */
export default function EmptyState({ children }: EmptyStateProps) {
  return (
    <div
      role="status"
      className="p-4 bg-gray-50 rounded border border-gray-200 text-sm text-gray-500"
    >
      {children}
    </div>
  );
}
