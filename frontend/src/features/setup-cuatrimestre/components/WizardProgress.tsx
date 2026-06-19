interface WizardProgressProps {
  pasos: readonly string[];
  pasoActual: number;
}

export default function WizardProgress({ pasos, pasoActual }: WizardProgressProps) {
  return (
    <div className="flex items-center gap-2 mb-6">
      {pasos.map((paso, idx) => {
        const isCompleted = idx < pasoActual;
        const isCurrent = idx === pasoActual;
        return (
          <div key={paso} className="flex items-center gap-2">
            <div
              className={`flex items-center justify-center w-8 h-8 rounded-full text-xs font-medium transition-colors ${
                isCompleted
                  ? 'bg-blue-600 text-white'
                  : isCurrent
                    ? 'bg-blue-100 text-blue-700 border-2 border-blue-600'
                    : 'bg-gray-100 text-gray-400'
              }`}
            >
              {isCompleted ? '✓' : idx + 1}
            </div>
            <span
              className={`text-xs ${
                isCurrent ? 'font-semibold text-blue-700' : 'text-gray-500'
              }`}
            >
              {paso}
            </span>
            {idx < pasos.length - 1 && (
              <div className={`w-6 h-0.5 ${idx < pasoActual ? 'bg-blue-600' : 'bg-gray-200'}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
