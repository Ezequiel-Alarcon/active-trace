/**
 * Barrel export de la capa UI (design system) — punto único de importación.
 *
 * Las páginas importan desde `@/shared/ui`, p. ej.:
 *   import { Button, StatusBadge, DataTable } from '@/shared/ui';
 */
export { default as Button } from './Button';
export type { ButtonVariant } from './Button';
export { default as TextField } from './TextField';
export { default as Badge } from './Badge';
export { default as StatusBadge } from './StatusBadge';
export { default as Card } from './Card';
export { default as PageHeader } from './PageHeader';
export { default as EmptyState } from './EmptyState';
export { default as KpiCard } from './KpiCard';
export { default as FilterBar } from './FilterBar';
export { default as DataTable } from './DataTable';
export type { Column } from './DataTable';
export { clasesEstado } from './estado-colores';
export type { EstadoSemantico } from './estado-colores';
