import type { ReactNode } from 'react';
import Badge from './Badge';
import { clasesEstado, type EstadoSemantico } from './estado-colores';

interface StatusBadgeProps {
  estado: EstadoSemantico;
  children?: ReactNode;
}

/**
 * Badge de estado semántico: aplica el color centralizado de `estado-colores`.
 * Garantiza que un mismo estado se vea idéntico en todas las vistas.
 */
export default function StatusBadge({ estado, children }: StatusBadgeProps) {
  return <Badge className={clasesEstado(estado)}>{children}</Badge>;
}
