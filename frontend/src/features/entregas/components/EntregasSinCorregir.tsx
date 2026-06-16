import { useState } from 'react';
import { useTpsSinCorregir, useUploadFinalizacion } from '../hooks/useEntregas';
import type { TpSinCorregirEntry } from '../types/entregas';

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

  const alumnos: TpSinCorregirEntry[] = data?.alumnos ?? [];
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
        <button
          type="button"
          disabled={!file || uploadMutation.isPending}
          onClick={handleUpload}
          className="self-start px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {uploadMutation.isPending ? 'Procesando…' : 'Cruzar con calificaciones'}
        </button>
      </div>

      {/* Table */}
      {/* Export button — always rendered, disabled when no data */}
      <div className="flex justify-end">
        <button
          type="button"
          onClick={handleExport}
          disabled={!hasData}
          className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
        >
          Exportar CSV
        </button>
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-500">Cargando entregas…</p>
      ) : !hasData ? (
        <div role="status" className="p-4 bg-gray-50 rounded border border-gray-200 text-sm text-gray-500">
          No se detectaron entregas sin corregir.
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          <p className="text-sm text-gray-600">{alumnos.length} entrega(s) sin corregir</p>
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="py-2 text-left font-medium text-gray-700">Usuario ID</th>
                <th className="py-2 text-left font-medium text-gray-700">Materia</th>
              </tr>
            </thead>
            <tbody>
              {alumnos.map((a, idx) => (
                <tr key={`${a.usuario_id ?? 'null'}-${idx}`} className="border-b border-gray-100">
                  <td className="py-2 text-gray-500">{a.usuario_id ?? '—'}</td>
                  <td className="py-2">{a.materia_nombre ?? a.materia_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
