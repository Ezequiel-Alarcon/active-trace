import type { HTMLAttributes } from 'react';

const BASE = 'rounded-xl border border-slate-200 bg-white p-5 shadow-sm';

/** Contenedor con borde, sombra y padding. */
export default function Card({ className = '', ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={`${BASE} ${className}`.trim()} {...props} />;
}
