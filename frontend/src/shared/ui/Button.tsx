import type { ButtonHTMLAttributes } from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'danger';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const VARIANTES: Record<ButtonVariant, string> = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700',
  secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-200',
  danger: 'bg-red-600 text-white hover:bg-red-700',
};

const BASE =
  'inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium ' +
  'transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none ' +
  'focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2';

/** Botón del design system. Variantes: primary (azul), secondary (gris), danger (rojo). */
export default function Button({
  variant = 'primary',
  type = 'button',
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button type={type} className={`${BASE} ${VARIANTES[variant]} ${className}`.trim()} {...props} />
  );
}
