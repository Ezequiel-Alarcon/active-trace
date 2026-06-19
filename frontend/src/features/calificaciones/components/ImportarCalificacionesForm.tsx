import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { usePreviewImport, useConfirmImport } from '../hooks/useImportarCalificaciones';
import type { CalificacionPreviewResponse } from '../types/calificaciones';
import { Button, Card } from '@/shared/ui';

interface ImportarCalificacionesFormProps {
  comisionId: string;
}

const umbralSchema = z.object({
  umbral: z
    .number({ invalid_type_error: 'Ingresá un número' })
    .min(0, 'El umbral debe ser ≥ 0')
    .max(100, 'El umbral debe ser ≤ 100'),
});

type UmbralFormValues = z.infer<typeof umbralSchema>;

/**
 * Multi-step form for importing calificaciones.
 * Step 1: upload file → preview
 * Step 2: select activities
 * Step 3: set umbral and confirm
 */
export default function ImportarCalificacionesForm({
  comisionId: _comisionId,
}: ImportarCalificacionesFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<CalificacionPreviewResponse | null>(null);
  const [selectedAsignaciones, setSelectedAsignaciones] = useState<Set<string>>(new Set());
  const [confirmedResult, setConfirmedResult] = useState<{ persisted: number; skipped: number; failed: number } | null>(null);

  const previewMutation = usePreviewImport();
  const confirmMutation = useConfirmImport();

  const {
    register,
    handleSubmit,
    formState: { errors },
    getValues,
  } = useForm<UmbralFormValues>({
    resolver: zodResolver(umbralSchema),
    defaultValues: { umbral: 60 },
  });

  // Derive unique asignacion_ids from preview rows
  const asignaciones = preview
    ? Array.from(
        new Set(preview.rows.map((r) => r.asignacion_id).filter(Boolean) as string[]),
      ).map((id) => ({ id, label: id }))
    : [];

  const allSelected = asignaciones.length > 0 && asignaciones.every((a) => selectedAsignaciones.has(a.id));

  function toggleAsignacion(id: string) {
    setSelectedAsignaciones((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleUpload() {
    if (!file) return;
    try {
      const result = await previewMutation.mutateAsync({ file });
      setPreview(result);
      // Pre-select all activities
      const ids = new Set(
        result.rows.map((r) => r.asignacion_id).filter(Boolean) as string[],
      );
      setSelectedAsignaciones(ids);
    } catch {
      // Error is captured in previewMutation.isError — no rethrow needed
    }
  }

  async function onConfirm(_values: UmbralFormValues) {
    if (!preview || selectedAsignaciones.size === 0) return;
    try {
      const result = await confirmMutation.mutateAsync(preview.preview_token);
      setConfirmedResult(result);
    } catch {
      // Error captured in confirmMutation.isError
    }
  }

  if (confirmedResult) {
    return (
      <div role="status" className="p-4 bg-green-50 rounded border border-green-200">
        <p className="text-green-800 font-medium">Importación completada</p>
        <p className="text-sm text-green-700">
          Persistidas: {confirmedResult.persisted} · Omitidas: {confirmedResult.skipped} · Fallidas: {confirmedResult.failed}
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-lg font-semibold text-gray-800">Importar calificaciones</h2>

      {/* Step 1: file upload */}
      <div className="flex flex-col gap-2">
        <label htmlFor="calificaciones-file" className="text-sm font-medium text-gray-700">
          Archivo de calificaciones (CSV)
        </label>
        <input
          id="calificaciones-file"
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="text-sm"
        />
        {previewMutation.isError && (
          <p role="alert" className="text-sm text-red-600">
            {(previewMutation.error as Error).message ?? 'Error al procesar el archivo.'}
          </p>
        )}
        <Button
          disabled={!file || previewMutation.isPending}
          onClick={handleUpload}
          className="self-start"
        >
          {previewMutation.isPending ? 'Procesando…' : 'Ver preview'}
        </Button>
      </div>

      {/* Step 2+3: preview + activity selection + umbral */}
      {preview && (
        <form onSubmit={handleSubmit(onConfirm)} className="flex flex-col gap-6">
          {/* Preview summary */}
          <Card>
            <p className="text-sm text-gray-700">
              Archivo: <strong>{preview.filename}</strong> · {preview.total} filas detectadas
            </p>
          </Card>

          {/* Activity selection */}
          <fieldset className="flex flex-col gap-2">
            <legend className="text-sm font-medium text-gray-700 mb-1">
              Seleccioná las actividades a incluir
            </legend>
            {asignaciones.length === 0 ? (
              <p className="text-sm text-gray-500">No se detectaron actividades.</p>
            ) : (
              asignaciones.map((a) => (
                <label key={a.id} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={selectedAsignaciones.has(a.id)}
                    onChange={() => toggleAsignacion(a.id)}
                  />
                  {a.label}
                </label>
              ))
            )}
          </fieldset>

          {/* Umbral */}
          <div className="flex flex-col gap-1">
            <label htmlFor="umbral" className="text-sm font-medium text-gray-700">
              Umbral de aprobación (%)
            </label>
            <input
              id="umbral"
              type="number"
              {...register('umbral', { valueAsNumber: true })}
              className="w-32 border border-gray-300 rounded px-3 py-1 text-sm"
            />
            {errors.umbral && (
              <p role="alert" className="text-sm text-red-600">{errors.umbral.message}</p>
            )}
          </div>

          <Button
            type="submit"
            disabled={selectedAsignaciones.size === 0 || confirmMutation.isPending}
            className="self-start"
          >
            {confirmMutation.isPending ? 'Confirmando…' : 'Confirmar y analizar'}
          </Button>

          {/* Keep file picker accessible even after preview — per spec */}
          <p className="text-xs text-gray-400">
            Umbral: {getValues('umbral')}% · Actividades seleccionadas: {selectedAsignaciones.size} / {asignaciones.length}
          </p>
        </form>
      )}
    </div>
  );
}
