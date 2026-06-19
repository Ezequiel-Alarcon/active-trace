import { forwardRef, type InputHTMLAttributes } from 'react';

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  id: string;
  label: string;
  /** Mensaje de error de validación (opcional). */
  error?: string;
}

const INPUT_BASE =
  'border border-gray-300 rounded px-3 py-2 text-sm ' +
  'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500';

/**
 * Campo de formulario: label + input + error.
 * Usa forwardRef para ser compatible con el `register` de react-hook-form.
 */
const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  { id, label, error, className = '', ...props },
  ref,
) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium text-gray-700">
        {label}
      </label>
      <input id={id} ref={ref} className={`${INPUT_BASE} ${className}`.trim()} {...props} />
      {error && <span className="text-red-600 text-xs">{error}</span>}
    </div>
  );
});

export default TextField;
