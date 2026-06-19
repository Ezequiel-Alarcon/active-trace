import type { HTMLAttributes } from 'react';

const BASE = 'inline-flex items-center rounded px-2 py-0.5 text-xs font-medium';

/** Pill genérico. Para estados semánticos usar `StatusBadge`. */
export default function Badge({ className = '', ...props }: HTMLAttributes<HTMLSpanElement>) {
  return <span className={`${BASE} ${className}`.trim()} {...props} />;
}
