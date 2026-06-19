import { useState } from 'react';
import { useHistorial, useDetalleHistorial } from '../hooks/useLiquidaciones';
import { PageHeader, DataTable, StatusBadge, Card, EmptyState, Button } from '@/shared/ui';
import type { Column } from '@/shared/ui';
import type { LiquidacionHistorialEntry } from '../types/liquidaciones';

export default function HistorialPage() {
  const { data, isLoading, isError } = useHistorial();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { data: detalle } = useDetalleHistorial(selectedId);

  const columns: Column<LiquidacionHistorialEntry>[] = [
    { header: 'Período', render: (h) => h.periodo },
    { header: 'Fecha cierre', render: (h) => new Date(h.fecha_cierre).toLocaleDateString() },
    { header: 'Total general', render: (h) => `$${h.total_general.toLocaleString()}` },
    { header: 'Total sin factura', render: (h) => `$${h.total_sin_factura.toLocaleString()}` },
    { header: 'Total con factura', render: (h) => `$${h.total_con_factura.toLocaleString()}` },
    { header: '', render: (h) => (
      <Button variant="secondary" onClick={() => setSelectedId(h.id)}>Ver detalle</Button>
    )},
  ];

  if (detalle && selectedId) {
    const detalleColumns: Column<{ label: string; value: string }>[] = [
      { header: 'Docente', render: (d) => d.label },
      { header: 'Total', render: (d) => d.value },
    ];

    return (
      <div className="flex flex-col gap-4">
        <PageHeader
          title={`Detalle de liquidación - ${detalle.periodo}`}
          actions={<Button variant="secondary" onClick={() => setSelectedId(null)}>Volver</Button>}
        />
        {detalle.segmentos.map((seg) => (
          <Card key={seg.segmento}>
            <h2 className="text-lg font-semibold mb-3">{seg.titulo}</h2>
            <DataTable
              rows={seg.docentes.map((d) => ({ label: d.nombre, value: `$${d.total.toLocaleString()}` }))}
              columns={detalleColumns}
              rowKey={(_, i) => `${seg.segmento}-${i}`}
            />
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Historial de liquidaciones" />

      {isLoading && <p className="text-sm text-gray-500">Cargando historial…</p>}
      {isError && <p role="alert" className="text-sm text-red-600">Error al cargar historial.</p>}

      {data && data.length === 0 ? (
        <EmptyState>No hay liquidaciones cerradas</EmptyState>
      ) : (
        <DataTable
          rows={data ?? []}
          columns={columns}
          rowKey={(h) => h.id}
        />
      )}
    </div>
  );
}
