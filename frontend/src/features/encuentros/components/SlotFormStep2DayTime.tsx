import { Card, TextField } from '@/shared/ui';
import { DAY_OPTIONS, MODALIDAD_OPTIONS } from './encuentrosFormUtils';

interface SlotFormStep2DayTimeProps {
  diaSemana: number;
  horaInicio: string;
  horaFin: string;
  modalidad: string;
  link: string;
  onFieldChange: (field: string, value: string | number) => void;
  errors: Record<string, string | undefined>;
  disabled?: boolean;
}

const SELECT_CLASS = 'border border-gray-300 rounded px-3 py-2 text-sm w-full';

export default function SlotFormStep2DayTime({
  diaSemana,
  horaInicio,
  horaFin,
  modalidad,
  link,
  onFieldChange,
  errors,
  disabled,
}: SlotFormStep2DayTimeProps) {
  return (
    <Card className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Paso 2 · Día y horario</h2>
        <p className="text-sm text-gray-600">Definí cuándo ocurre el encuentro y cómo se accede.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="flex flex-col gap-1">
          <label htmlFor="dia_semana" className="text-sm font-medium text-gray-700">
            Día de la semana
          </label>
          <select
            id="dia_semana"
            value={String(diaSemana)}
            onChange={(event) => onFieldChange('dia_semana', Number(event.target.value))}
            className={SELECT_CLASS}
            disabled={disabled}
          >
            {DAY_OPTIONS.map((day) => (
              <option key={day.value} value={day.value}>
                {day.label}
              </option>
            ))}
          </select>
          {errors.dia_semana && <p className="text-xs text-red-600">{errors.dia_semana}</p>}
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="modalidad" className="text-sm font-medium text-gray-700">
            Modalidad
          </label>
          <select
            id="modalidad"
            value={modalidad}
            onChange={(event) => onFieldChange('modalidad', event.target.value)}
            className={SELECT_CLASS}
            disabled={disabled}
          >
            {MODALIDAD_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <TextField
          id="hora_inicio"
          label="Hora de inicio"
          type="time"
          value={horaInicio}
          onChange={(event) => onFieldChange('hora_inicio', event.target.value)}
          error={errors.hora_inicio}
          disabled={disabled}
        />
        <TextField
          id="hora_fin"
          label="Hora de fin"
          type="time"
          value={horaFin}
          onChange={(event) => onFieldChange('hora_fin', event.target.value)}
          error={errors.hora_fin}
          disabled={disabled}
        />
      </div>

      <TextField
        id="link"
        label="Enlace"
        type="url"
        placeholder={modalidad === 'presencial' ? 'Opcional para modalidad presencial' : 'https://...'}
        value={link}
        onChange={(event) => onFieldChange('link', event.target.value)}
        error={errors.link}
        disabled={disabled}
      />
    </Card>
  );
}
