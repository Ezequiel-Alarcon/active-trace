import { useState } from 'react';
import { PageHeader, Button, Card } from '@/shared/ui';
import { useGuardias } from '../hooks/useGuardias';
import TablaGuardias from '../components/TablaGuardias';
import GuardiaForm from '../components/GuardiaForm';

export default function GuardiasPage() {
  const [showForm, setShowForm] = useState(false);
  const { data, isLoading, isError } = useGuardias();

  const guardias = data ?? [];

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="Mis Guardias"
        actions={
          !showForm ? (
            <Button onClick={() => setShowForm(true)}>+ Nueva guardia</Button>
          ) : null
        }
      />

      {showForm && (
        <Card>
          <h2 className="text-lg font-medium text-gray-800 mb-4">Registrar guardia</h2>
          <GuardiaForm
            onSuccess={() => setShowForm(false)}
            onCancel={() => setShowForm(false)}
          />
        </Card>
      )}

      {isLoading && <p className="text-sm text-gray-500">Cargando…</p>}
      {isError && <p className="text-sm text-red-500">Error al cargar los datos.</p>}
      {!isLoading && !isError && <TablaGuardias guardias={guardias} />}
    </div>
  );
}
