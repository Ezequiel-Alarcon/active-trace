import { useState } from 'react';
import { useLiquidacionPeriodo } from '../hooks/useLiquidaciones';
import { useCarreras } from '@/features/admin/hooks/useEstructura';
import { PageHeader, FilterBar, KpiCard, DataTable, StatusBadge, Card, Button, EmptyState } from '@/shared/ui';
import type { Column } from '@/shared/ui';
import type { LiquidacionDocenteEntry } from '../types/liquidaciones';
import CerrarLiquidacionDialog from '../components/CerrarLiquidacionDialog';

export default function LiquidacionPeriodoPage() {
  const [cohorteId, setCohorteId] = useState('');
  const [mes, setMes] = useState('');
  const [docenteId, setDocenteId] = useState('');
  const { data: carreras } = useCarreras();
  const { data, isLoading, isError } = useLiquidacionPeriodo(cohorteId, mes, docenteId || undefined);
  const [showCerrar, setShowCerrar] = useState(false);

  const columns: Column<LiquidacionDocenteEntry>[] = [
    { header: 'Docente', render: (d) => d.nombre },
    { header: 'Rol', render: (d) => d.rol },
    { header: 'Comisiones', render: (d) => d.comisiones.join(', ') },
    { header: 'Salario Base', render: (d) => `$${d.salario_base.toLocaleString()}` },
    { header: 'Plus', render: (d) => `$${d.salario_plus.toLocaleString()}` },
    { header: 'Total', render: (d) => <span className="font-semibold">${d.total.toLocaleString()}</span> },
  ];

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="Liquidaciones del período"
        actions={
          data?.estado === 'Abierta' ? (
            <Button variant="danger" onClick={() => setShowCerrar(true)}>
              Cerrar liquidación
            </Button>
          ) : data?.estado === 'Cerrada' ? (
            <StatusBadge estado="enviado">Cerrada</StatusBadge>
          ) : null
        }
      />

      <FilterBar>
        <select
          className="border border-gray-200 rounded px-3 py-1.5 text-sm"
          value={cohorteId}
          onChange={(e) => setCohorteId(e.target.value)}
          aria-label="Cohorte"
        >
          <option value="">Seleccionar cohorte</option>
          {carreras?.map((c) => (
            <option key={c.id} value={c.id}>{c.nombre}</option>
          ))}
        </select>
        <input
          type="month"
          className="border border-gray-200 rounded px-3 py-1.5 text-sm"
          value={mes}
          onChange={(e) => setMes(e.target.value)}
          aria-label="Mes"
          placeholder="Mes"
        />
        <input
          type="text"
          className="border border-gray-200 rounded px-3 py-1.5 text-sm"
          value={docenteId}
          onChange={(e) => setDocenteId(e.target.value)}
          placeholder="Docente (opcional)"
          aria-label="Docente"
        />
      </FilterBar>

      {isLoading && <p className="text-sm text-gray-500">Cargando liquidaciones…</p>}
      {isError && <p role="alert" className="text-sm text-red-600">Error al cargar liquidaciones.</p>}

      {data && (
        <>
          <div className="flex gap-4">
            <KpiCard label="Total sin factura" value={`$${data.total_sin_factura.toLocaleString()}`} />
            <KpiCard label="Universo facturante" value={`$${data.universo_facturante.toLocaleString()}`} />
          </div>

          {data.segmentos.map((seg) => (
            <Card key={seg.segmento}>
              <h2 className="text-lg font-semibold mb-3">{seg.titulo}</h2>
              {seg.docentes.length === 0 ? (
                <EmptyState>No hay docentes en este segmento.</EmptyState>
              ) : (
                <DataTable
                  rows={seg.docentes}
                  columns={columns}
                  rowKey={(d, i) => `${seg.segmento}-${d.usuario_id}-${i}`}
                />
              )}
            </Card>
          ))}
        </>
      )}

      {showCerrar && (
        <CerrarLiquidacionDialog
          periodo={data?.periodo ?? ''}
          onClose={() => setShowCerrar(false)}
        />
      )}
    </div>
  );
}
