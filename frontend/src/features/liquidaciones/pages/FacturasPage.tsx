import { useState } from 'react';
import { useFacturas } from '../hooks/useFacturas';
import { PageHeader, FilterBar, DataTable, StatusBadge, Button, EmptyState } from '@/shared/ui';
import type { Column } from '@/shared/ui';
import type { Factura } from '../types/liquidaciones';
import FacturaFormModal from '../components/FacturaFormModal';
import MarcarAbonadaDialog from '../components/MarcarAbonadaDialog';

export default function FacturasPage() {
  const [docenteId, setDocenteId] = useState('');
  const [estado, setEstado] = useState('');
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');
  const { data, isLoading, isError } = useFacturas(docenteId || undefined, estado || undefined, desde || undefined, hasta || undefined);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [marcarAbonadaId, setMarcarAbonadaId] = useState<string | null>(null);

  const columns: Column<Factura>[] = [
    { header: 'Fecha carga', render: (f) => new Date(f.fecha_carga).toLocaleDateString() },
    { header: 'Docente', render: (f) => f.docente_nombre },
    { header: 'Período', render: (f) => f.periodo },
    { header: 'Detalle', render: (f) => f.detalle },
    {
      header: 'Estado',
      render: (f) => (
        <StatusBadge estado={f.estado === 'Abonada' ? 'enviado' : 'pendiente'}>
          {f.estado}
        </StatusBadge>
      ),
    },
    {
      header: 'Acciones',
      render: (f) =>
        f.estado === 'Pendiente' ? (
          <Button variant="secondary" onClick={() => setMarcarAbonadaId(f.id)}>
            Marcar abonada
          </Button>
        ) : null,
    },
  ];

  function handleLimpiar() {
    setDocenteId('');
    setEstado('');
    setDesde('');
    setHasta('');
  }

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="Facturas"
        actions={<Button onClick={() => setShowCreateModal(true)}>Registrar factura</Button>}
      />

      <FilterBar>
        <input
          type="text"
          className="border border-gray-200 rounded px-3 py-1.5 text-sm"
          value={docenteId}
          onChange={(e) => setDocenteId(e.target.value)}
          placeholder="Docente"
          aria-label="Docente"
        />
        <select
          className="border border-gray-200 rounded px-3 py-1.5 text-sm"
          value={estado}
          onChange={(e) => setEstado(e.target.value)}
          aria-label="Estado"
        >
          <option value="">Todos los estados</option>
          <option value="Pendiente">Pendiente</option>
          <option value="Abonada">Abonada</option>
        </select>
        <div>
          <label className="text-xs text-gray-500">Desde</label>
          <input
            type="date"
            className="border border-gray-200 rounded px-3 py-1.5 text-sm"
            value={desde}
            onChange={(e) => setDesde(e.target.value)}
            aria-label="Desde"
          />
        </div>
        <div>
          <label className="text-xs text-gray-500">Hasta</label>
          <input
            type="date"
            className="border border-gray-200 rounded px-3 py-1.5 text-sm"
            value={hasta}
            onChange={(e) => setHasta(e.target.value)}
            aria-label="Hasta"
          />
        </div>
        <Button variant="secondary" onClick={handleLimpiar}>Limpiar filtros</Button>
      </FilterBar>

      {isLoading && <p className="text-sm text-gray-500">Cargando facturas…</p>}
      {isError && <p role="alert" className="text-sm text-red-600">Error al cargar facturas.</p>}

      {data && data.length === 0 ? (
        <EmptyState>No hay facturas para los filtros seleccionados</EmptyState>
      ) : (
        <DataTable rows={data ?? []} columns={columns} rowKey={(f) => f.id} />
      )}

      {showCreateModal && <FacturaFormModal onClose={() => setShowCreateModal(false)} />}
      {marcarAbonadaId && (
        <MarcarAbonadaDialog facturaId={marcarAbonadaId} onClose={() => setMarcarAbonadaId(null)} />
      )}
    </div>
  );
}
