/**
 * Colores semánticos de estado — fuente única de verdad del design system.
 *
 * Ninguna página debe definir colores de estado ad-hoc: todas consumen este
 * mapa (vía `StatusBadge`) para que un mismo estado se vea idéntico en cualquier
 * vista (atrasados, monitor, comunicaciones, etc.).
 *
 * Convención de color:
 *   rojo  → atrasado / fallido
 *   verde → aprobado / enviado
 *   ámbar → pendiente / cancelado
 *   azul  → en-envio (acento primario)
 *   gris  → pendiente-cola / neutro
 */
export type EstadoSemantico =
  | 'atrasado'
  | 'fallido'
  | 'aprobado'
  | 'enviado'
  | 'pendiente'
  | 'cancelado'
  | 'en-envio'
  | 'pendiente-cola'
  | 'en-progreso'
  | 'resuelta'
  | 'neutro';

const CLASES_POR_ESTADO: Record<EstadoSemantico, string> = {
  atrasado: 'bg-red-100 text-red-700',
  fallido: 'bg-red-100 text-red-700',
  aprobado: 'bg-green-100 text-green-700',
  enviado: 'bg-green-100 text-green-700',
  pendiente: 'bg-amber-100 text-amber-700',
  cancelado: 'bg-amber-100 text-amber-700',
  'en-envio': 'bg-blue-100 text-blue-700',
  'pendiente-cola': 'bg-gray-100 text-gray-700',
  'en-progreso': 'bg-blue-100 text-blue-700',
  resuelta: 'bg-green-100 text-green-700',
  neutro: 'bg-gray-100 text-gray-700',
};

/** Devuelve las clases Tailwind de badge para un estado semántico. */
export function clasesEstado(estado: EstadoSemantico): string {
  return CLASES_POR_ESTADO[estado];
}
