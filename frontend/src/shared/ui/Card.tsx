import type { HTMLAttributes } from 'react';

const BASE = 'rounded-lg border border-gray-200 bg-white p-4';

/** Contenedor con borde y padding. */
export default function Card({ className = '', ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={`${BASE} ${className}`.trim()} {...props} />;
}
