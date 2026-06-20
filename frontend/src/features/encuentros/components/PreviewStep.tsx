import { Card } from '@/shared/ui';
import type { SlotFormValues } from '../types/encuentros';
import { DAY_OPTIONS } from './encuentrosFormUtils';

interface PreviewStepProps {
  values: SlotFormValues;
}

interface PreviewRow {
  fecha: string;
  hora_inicio: string;
  hora_fin: string;
  titulo: string;
}

function parseIsoDate(date: string) {
  const [year, month, day] = date.split('-').map(Number);
  return new Date(Date.UTC(year, month - 1, day));
}

function formatIsoDate(date: Date) {
  return date.toISOString().slice(0, 10);
}

export function buildPreviewRows(values: SlotFormValues): PreviewRow[] {
  if (!values.fecha_inicio || values.cant_semanas < 1) {
    return [];
  }

  const startDate = parseIsoDate(values.fecha_inicio);
  if (Number.isNaN(startDate.getTime())) {
    return [];
  }

  return Array.from({ length: Number(values.cant_semanas) }, (_, index) => {
    const current = new Date(startDate);
    current.setUTCDate(startDate.getUTCDate() + index * 7);

    return {
      fecha: formatIsoDate(current),
      hora_inicio: values.hora_inicio,
      hora_fin: values.hora_fin,
      titulo: values.titulo,
    };
  });
}

export default function PreviewStep({ values }: PreviewStepProps) {
  const rows = buildPreviewRows(values);
  const dia = DAY_OPTIONS.find((option) => option.value === Number(values.dia_semana))?.label ?? '—';

  return (
    <Card className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Paso 4 · Preview</h2>
        <p className="text-sm text-gray-600">
          Se crearán {rows.length} instancias para {dia} con el título “{values.titulo || 'Sin título'}”.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead>
            <tr className="text-left text-gray-600">
              <th className="px-3 py-2 font-medium">Fecha</th>
              <th className="px-3 py-2 font-medium">Hora inicio</th>
              <th className="px-3 py-2 font-medium">Hora fin</th>
              <th className="px-3 py-2 font-medium">Título</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rows.map((row) => (
              <tr key={`${row.fecha}-${row.hora_inicio}`}>
                <td className="px-3 py-2">{row.fecha}</td>
                <td className="px-3 py-2">{row.hora_inicio}</td>
                <td className="px-3 py-2">{row.hora_fin}</td>
                <td className="px-3 py-2">{row.titulo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
