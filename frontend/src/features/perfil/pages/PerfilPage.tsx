import { PageHeader } from '@/shared/ui';
import PerfilForm from '../components/PerfilForm';

export default function PerfilPage() {
  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Mi Perfil" />
      <PerfilForm />
    </div>
  );
}
