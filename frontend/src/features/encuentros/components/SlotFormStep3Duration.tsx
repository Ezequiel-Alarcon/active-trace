import { Card, TextField } from '@/shared/ui';

interface SlotFormStep3DurationProps {
  fechaInicio: string;
  cantSemanas: number;
  titulo: string;
  onFieldChange: (field: string, value: string | number) => void;
  errors: Record<string, string | undefined>;
  disabled?: boolean;
}

export default function SlotFormStep3Duration({
  fechaInicio,
  cantSemanas,
  titulo,
  onFieldChange,
  errors,
  disabled,
}: SlotFormStep3DurationProps) {
  return (
    <Card className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Paso 3 · Duración y título</h2>
        <p className="text-sm text-gray-600">Definí desde cuándo arranca el slot y cuántas semanas dura.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <TextField
          id="fecha_inicio"
          label="Fecha de inicio"
          type="date"
          value={fechaInicio}
          onChange={(event) => onFieldChange('fecha_inicio', event.target.value)}
          error={errors.fecha_inicio}
          disabled={disabled}
        />
        <TextField
          id="cant_semanas"
          label="Cantidad de semanas"
          type="number"
          min={1}
          max={52}
          value={String(cantSemanas)}
          onChange={(event) => onFieldChange('cant_semanas', Number(event.target.value))}
          error={errors.cant_semanas}
          disabled={disabled}
        />
      </div>

      <TextField
        id="titulo"
        label="Título"
        placeholder="Teórica, práctica, apoyo, etc."
        value={titulo}
        onChange={(event) => onFieldChange('titulo', event.target.value)}
        error={errors.titulo}
        disabled={disabled}
      />
    </Card>
  );
}
