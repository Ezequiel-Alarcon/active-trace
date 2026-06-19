import { useState } from 'react';
import { useTpsSinCorregir, useUploadFinalizacion } from '../hooks/useEntregas';
import { Button, DataTable, StatusBadge, type Column } from '@/shared/ui';

interface EntregasSinCorregirProps {
  comisionId: string;
}

/**
 * Component for uploading finalizacion report and viewing uncorrected submissions.
 */
export default function EntregasSinCorregir({ comisionId: _comisionId }: EntregasSinCorregirProps) {
  const [file, setFile] = useState<File | null>(null);
  const { data, isLoading, refetch } = useTpsSinCorregir();
  const uploadMutation = useUploadFinalizacion();

  const alumnos = data?.alumnos ?? [];
  const hasData = alumnos.length > 0;

  async function handleUpload() {
    if (!file) return;
    await uploadMutation.mutateAsync(file);
    refetch();
  }

  function handleExport() {
    if (!hasData) return;
    const csv = [
      'usuario_id,materia_id,materia_nombre',
      ...alumnos.map((a) => `${a.usuario_id ?? ''},${a.materia_id},${a.materia_nombre ?? ''}`),
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'entregas-sin-corregir.csv';
    a.click();
    URL.revokeObjectURL(url);
  }

  const columns: Column<(typeof alumnos)[number]>[] = [
    { header: 'Usuario ID', render: (a) => <span className="text-gray-500">{a.usuario_id ?? '—'}</span> },
    { header: 'Materia', render: (a) => a.materia_nombre ?? a.materia_id },
    { header: 'Estado', render: () => <StatusBadge estado="pendiente">Sin corregir</StatusBadge> },
  ];

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-lg font-semibold text-gray-800">Entregas sin corregir</h2>

      {/* Upload finalización report */}
      <div className="flex flex-col gap-2">
        <label htmlFor="finalizacion-file" className="text-sm font-medium text-gray-700">
          Reporte de finalización (CSV)
        </label>
        <input
          id="finalizacion-file"
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="text-sm"
        />
        <Button
          disabled={!file || uploadMutation.isPending}
          onClick={handleUpload}
          className="self-start"
        >
          {uploadMutation.isPending ? 'Procesando…' : 'Cruzar con calificaciones'}
        </Button>
      </div>

      {/* Export button — always rendered, disabled when no data */}
      <div className="flex justify-end">
        <Button variant="secondary" onClick={handleExport} disabled={!hasData}>
          Exportar CSV
        </Button>
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-500">Cargando entregas…</p>
      ) : (
        <div className="flex flex-col gap-2">
          {hasData && (
            <p className="text-sm text-gray-600">{alumnos.length} entrega(s) sin corregir</p>
          )}
          <DataTable
            rows={alumnos}
            columns={columns}
            rowKey={(a, idx) => `${a.usuario_id ?? 'null'}-${idx}`}
            emptyMessage="No se detectaron entregas sin corregir."
          />
        </div>
      )}
    </div>
  );
}
