import { useState } from 'react';
import { useCarreras, useDeleteCarrera, useCohortes, useDeleteCohorte, useMaterias, useDeleteMateria } from '../hooks/useEstructura';
import { PageHeader, DataTable, StatusBadge, Button, EmptyState } from '@/shared/ui';
import type { Column } from '@/shared/ui';
import type { Carrera, Cohorte, Materia } from '../types/estructura';
import CarreraFormModal from '../components/CarreraFormModal';
import CohorteFormModal from '../components/CohorteFormModal';
import MateriaFormModal from '../components/MateriaFormModal';

type Tab = 'carreras' | 'cohortes' | 'materias';

export default function EstructuraPage() {
  const [tab, setTab] = useState<Tab>('carreras');
  const { data: carreras, isLoading: loadingCarreras } = useCarreras();
  const deleteCarrera = useDeleteCarrera();
  const { data: materias, isLoading: loadingMaterias } = useMaterias();
  const deleteMateria = useDeleteMateria();

  const [filterCarreraId, setFilterCarreraId] = useState('');
  const { data: cohortes, isLoading: loadingCohortes } = useCohortes(filterCarreraId || undefined);
  const deleteCohorte = useDeleteCohorte();

  const [showCarreraModal, setShowCarreraModal] = useState(false);
  const [editCarrera, setEditCarrera] = useState<Carrera | null>(null);
  const [showCohorteModal, setShowCohorteModal] = useState(false);
  const [editCohorte, setEditCohorte] = useState<Cohorte | null>(null);
  const [showMateriaModal, setShowMateriaModal] = useState(false);
  const [editMateria, setEditMateria] = useState<Materia | null>(null);

  const carreraColumns: Column<Carrera>[] = [
    { header: 'Código', render: (c) => c.codigo },
    { header: 'Nombre', render: (c) => c.nombre },
    { header: 'Estado', render: (c) => <StatusBadge estado={c.estado === 'Activa' ? 'aprobado' : 'cancelado'}>{c.estado}</StatusBadge> },
    { header: 'Acciones', render: (c) => (
      <div className="flex gap-2">
        <Button variant="secondary" onClick={() => { setEditCarrera(c); setShowCarreraModal(true); }}>Editar</Button>
        <Button variant="danger" onClick={() => deleteCarrera.mutate(c.id)}>Eliminar</Button>
      </div>
    )},
  ];

  const cohorteColumns: Column<Cohorte>[] = [
    { header: 'Nombre', render: (c) => c.nombre },
    { header: 'Año', render: (c) => c.anio },
    { header: 'Vigencia desde', render: (c) => c.vig_desde },
    { header: 'Vigencia hasta', render: (c) => c.vig_hasta ?? '—' },
    { header: 'Estado', render: (c) => <StatusBadge estado="neutro">{c.estado}</StatusBadge> },
    { header: 'Acciones', render: (c) => (
      <div className="flex gap-2">
        <Button variant="secondary" onClick={() => { setEditCohorte(c); setShowCohorteModal(true); }}>Editar</Button>
        <Button variant="danger" onClick={() => deleteCohorte.mutate(c.id)}>Eliminar</Button>
      </div>
    )},
  ];

  const materiaColumns: Column<Materia>[] = [
    { header: 'Código', render: (m) => m.codigo },
    { header: 'Nombre', render: (m) => m.nombre },
    { header: 'Estado', render: (m) => <StatusBadge estado="neutro">{m.estado}</StatusBadge> },
    { header: 'Acciones', render: (m) => (
      <div className="flex gap-2">
        <Button variant="secondary" onClick={() => { setEditMateria(m); setShowMateriaModal(true); }}>Editar</Button>
        <Button variant="danger" onClick={() => deleteMateria.mutate(m.id)}>Eliminar</Button>
      </div>
    )},
  ];

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Estructura académica" />

      <div className="flex gap-2 border-b border-gray-200 pb-2">
        {(['carreras', 'cohortes', 'materias'] as const).map((t) => (
          <button
            key={t}
            className={`px-4 py-2 text-sm rounded-t ${tab === t ? 'bg-blue-100 text-blue-700 font-medium' : 'text-gray-600 hover:bg-gray-100'}`}
            onClick={() => setTab(t)}
          >
            {t === 'carreras' ? 'Carreras' : t === 'cohortes' ? 'Cohortes' : 'Materias'}
          </button>
        ))}
      </div>

      {tab === 'carreras' && (
        <div>
          <div className="mb-3"><Button onClick={() => { setEditCarrera(null); setShowCarreraModal(true); }}>Agregar carrera</Button></div>
          {loadingCarreras && <p className="text-sm text-gray-500">Cargando…</p>}
          {!loadingCarreras && (!carreras || carreras.length === 0) ? (
            <EmptyState>No hay carreras registradas.</EmptyState>
          ) : (
            <DataTable rows={carreras ?? []} columns={carreraColumns} rowKey={(c) => c.id} />
          )}
        </div>
      )}

      {tab === 'cohortes' && (
        <div>
          <div className="flex gap-3 mb-3 items-end">
            <select className="border border-gray-200 rounded px-3 py-1.5 text-sm" value={filterCarreraId} onChange={(e) => setFilterCarreraId(e.target.value)} aria-label="Carrera">
              <option value="">Seleccionar carrera</option>
              {carreras?.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
            <Button onClick={() => { setEditCohorte(null); setShowCohorteModal(true); }} disabled={!filterCarreraId}>Agregar cohorte</Button>
          </div>
          {loadingCohortes && <p className="text-sm text-gray-500">Cargando…</p>}
          {!loadingCohortes && (!cohortes || cohortes.length === 0) ? (
            <EmptyState>No hay cohortes para la carrera seleccionada.</EmptyState>
          ) : (
            <DataTable rows={cohortes ?? []} columns={cohorteColumns} rowKey={(c) => c.id} />
          )}
        </div>
      )}

      {tab === 'materias' && (
        <div>
          <div className="mb-3"><Button onClick={() => { setEditMateria(null); setShowMateriaModal(true); }}>Agregar materia</Button></div>
          {loadingMaterias && <p className="text-sm text-gray-500">Cargando…</p>}
          {!loadingMaterias && (!materias || materias.length === 0) ? (
            <EmptyState>No hay materias registradas.</EmptyState>
          ) : (
            <DataTable rows={materias ?? []} columns={materiaColumns} rowKey={(m) => m.id} />
          )}
        </div>
      )}

      {showCarreraModal && <CarreraFormModal carrera={editCarrera} onClose={() => { setShowCarreraModal(false); setEditCarrera(null); }} />}
      {showCohorteModal && <CohorteFormModal cohorte={editCohorte} carreras={carreras ?? []} onClose={() => { setShowCohorteModal(false); setEditCohorte(null); }} />}
      {showMateriaModal && <MateriaFormModal materia={editMateria} onClose={() => { setShowMateriaModal(false); setEditMateria(null); }} />}
    </div>
  );
}
