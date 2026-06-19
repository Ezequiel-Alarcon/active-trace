import { useState } from 'react';
import { useUsuarios, useDeleteUsuario } from '../hooks/useUsuarios';
import { PageHeader, DataTable, Button, StatusBadge, EmptyState } from '@/shared/ui';
import type { Column } from '@/shared/ui';
import type { UsuarioTenant } from '../types/usuarios';
import UsuarioFormModal from '../components/UsuarioFormModal';

export default function UsuariosPage() {
  const { data: usuarios, isLoading } = useUsuarios();
  const deleteUsuario = useDeleteUsuario();
  const [showModal, setShowModal] = useState(false);
  const [editUser, setEditUser] = useState<UsuarioTenant | null>(null);

  // TODO: (BUG) DNI se muestra en texto plano pero es PII sensible (AES-256 en backend).
  // Según ARQUITECTURA.md §5.4, DNI/CBU deben estar cifrados. El frontend no debe
  // mostrar DNI sin descifrar — crear un componente DescriptedDNI o enmascarar.
  const columns: Column<UsuarioTenant>[] = [
    { header: 'Email', render: (u) => u.email },
    { header: 'Nombre', render: (u) => `${u.nombre} ${u.apellidos}` },
    { header: 'DNI', render: (u) => u.dni }, // TODO: (BUG) PII expuesta sin descifrar
    { header: 'Roles', render: (u) => (
      <div className="flex gap-1 flex-wrap">
        {u.roles.map((r) => (
          <StatusBadge key={r} estado="neutro">{r}</StatusBadge>
        ))}
      </div>
    )},
    { header: 'Estado', render: (u) => (
      <StatusBadge estado={u.estado === 'Activo' ? 'aprobado' : 'cancelado'}>{u.estado}</StatusBadge>
    )},
    { header: 'Acciones', render: (u) => (
      <div className="flex gap-2">
        <Button variant="secondary" onClick={() => { setEditUser(u); setShowModal(true); }}>Editar</Button>
        <Button variant="danger" onClick={() => deleteUsuario.mutate(u.id)}>Eliminar</Button>
      </div>
    )},
  ];

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Usuarios" />
      <div className="mb-3"><Button onClick={() => { setEditUser(null); setShowModal(true); }}>Agregar usuario</Button></div>
      {isLoading && <p className="text-sm text-gray-500">Cargando…</p>}
      {!isLoading && (!usuarios || usuarios.length === 0) ? (
        <EmptyState>No hay usuarios registrados en este tenant.</EmptyState>
      ) : (
        <DataTable rows={usuarios ?? []} columns={columns} rowKey={(u) => u.id} />
      )}
      {showModal && <UsuarioFormModal usuario={editUser} onClose={() => { setShowModal(false); setEditUser(null); }} />}
    </div>
  );
}
