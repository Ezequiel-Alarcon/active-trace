import { useState } from 'react';
import { useSalariosBase, useDeleteSalarioBase, useSalariosPlus, useDeleteSalarioPlus } from '../hooks/useGrillaSalarial';
import { PageHeader, DataTable, Button, Card, EmptyState } from '@/shared/ui';
import type { Column } from '@/shared/ui';
import type { SalarioBase, SalarioPlus } from '../types/liquidaciones';
import SalarioBaseFormModal from '../components/SalarioBaseFormModal';
import SalarioPlusFormModal from '../components/SalarioPlusFormModal';

type Tab = 'base' | 'plus';

export default function GrillaSalarialPage() {
  const [tab, setTab] = useState<Tab>('base');
  const { data: salariosBase, isLoading: loadingBase } = useSalariosBase();
  const { data: salariosPlus, isLoading: loadingPlus } = useSalariosPlus();
  const deleteBase = useDeleteSalarioBase();
  const deletePlus = useDeleteSalarioPlus();

  const [showBaseModal, setShowBaseModal] = useState(false);
  const [editBase, setEditBase] = useState<SalarioBase | null>(null);
  const [showPlusModal, setShowPlusModal] = useState(false);
  const [editPlus, setEditPlus] = useState<SalarioPlus | null>(null);

  const baseColumns: Column<SalarioBase>[] = [
    { header: 'Rol', render: (s) => s.rol },
    { header: 'Importe', render: (s) => `$${s.importe.toLocaleString()}` },
    { header: 'Vigencia desde', render: (s) => s.vigencia_desde },
    { header: 'Vigencia hasta', render: (s) => s.vigencia_hasta ?? '—' },
    {
      header: 'Acciones',
      render: (s) => (
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => { setEditBase(s); setShowBaseModal(true); }}>
            Editar
          </Button>
          <Button variant="danger" onClick={() => deleteBase.mutate(s.id)}>
            Eliminar
          </Button>
        </div>
      ),
    },
  ];

  const plusColumns: Column<SalarioPlus>[] = [
    { header: 'Clave', render: (s) => s.clave },
    { header: 'Rol', render: (s) => s.rol },
    { header: 'Descripción', render: (s) => s.descripcion },
    { header: 'Importe', render: (s) => `$${s.importe.toLocaleString()}` },
    { header: 'Vigencia desde', render: (s) => s.vigencia_desde },
    { header: 'Vigencia hasta', render: (s) => s.vigencia_hasta ?? '—' },
    {
      header: 'Acciones',
      render: (s) => (
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => { setEditPlus(s); setShowPlusModal(true); }}>
            Editar
          </Button>
          <Button variant="danger" onClick={() => deletePlus.mutate(s.id)}>
            Eliminar
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Grilla salarial" />

      <div className="flex gap-2 border-b border-gray-200 pb-2">
        <button
          className={`px-4 py-2 text-sm rounded-t ${tab === 'base' ? 'bg-blue-100 text-blue-700 font-medium' : 'text-gray-600 hover:bg-gray-100'}`}
          onClick={() => setTab('base')}
        >
          Salario Base
        </button>
        <button
          className={`px-4 py-2 text-sm rounded-t ${tab === 'plus' ? 'bg-blue-100 text-blue-700 font-medium' : 'text-gray-600 hover:bg-gray-100'}`}
          onClick={() => setTab('plus')}
        >
          Plus
        </button>
      </div>

      {tab === 'base' && (
        <div>
          <div className="mb-3">
            <Button onClick={() => { setEditBase(null); setShowBaseModal(true); }}>
              Agregar Salario Base
            </Button>
          </div>
          {loadingBase && <p className="text-sm text-gray-500">Cargando…</p>}
          {!loadingBase && (!salariosBase || salariosBase.length === 0) ? (
            <EmptyState>No hay salarios base registrados.</EmptyState>
          ) : (
            <DataTable rows={salariosBase ?? []} columns={baseColumns} rowKey={(s) => s.id} />
          )}
        </div>
      )}

      {tab === 'plus' && (
        <div>
          <div className="mb-3">
            <Button onClick={() => { setEditPlus(null); setShowPlusModal(true); }}>
              Agregar Plus
            </Button>
          </div>
          {loadingPlus && <p className="text-sm text-gray-500">Cargando…</p>}
          {!loadingPlus && (!salariosPlus || salariosPlus.length === 0) ? (
            <EmptyState>No hay plus registrados.</EmptyState>
          ) : (
            <DataTable rows={salariosPlus ?? []} columns={plusColumns} rowKey={(s) => s.id} />
          )}
        </div>
      )}

      {showBaseModal && (
        <SalarioBaseFormModal
          salario={editBase}
          onClose={() => { setShowBaseModal(false); setEditBase(null); }}
        />
      )}
      {showPlusModal && (
        <SalarioPlusFormModal
          salario={editPlus}
          onClose={() => { setShowPlusModal(false); setEditPlus(null); }}
        />
      )}
    </div>
  );
}
