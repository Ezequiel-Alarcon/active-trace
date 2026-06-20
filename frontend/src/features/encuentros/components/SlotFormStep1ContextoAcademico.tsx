import { Card } from '@/shared/ui';
import CohorteSelector from './CohorteSelector';
import MateriaSelector from './MateriaSelector';

interface SlotFormStep1ContextoAcademicoProps {
  materiaId: string;
  cohorteId: string;
  onMateriaChange: (value: string) => void;
  onCohorteChange: (value: string) => void;
  materiaError?: string;
  cohorteError?: string;
  disabled?: boolean;
}

export default function SlotFormStep1ContextoAcademico({
  materiaId,
  cohorteId,
  onMateriaChange,
  onCohorteChange,
  materiaError,
  cohorteError,
  disabled,
}: SlotFormStep1ContextoAcademicoProps) {
  return (
    <Card className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Paso 1 · Contexto académico</h2>
        <p className="text-sm text-gray-600">
          Elegí la materia y la cohorte explícitamente. No se infiere una desde la otra.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <MateriaSelector
          value={materiaId}
          onChange={onMateriaChange}
          error={materiaError}
          disabled={disabled}
        />
        <CohorteSelector
          value={cohorteId}
          onChange={onCohorteChange}
          error={cohorteError}
          disabled={disabled}
        />
      </div>
    </Card>
  );
}
