import { useOutletContext } from 'react-router-dom';
import TablaAtrasados from '../components/TablaAtrasados';

interface ComisionContext {
  comisionId: string;
}

export default function AtrasadosPage() {
  const { comisionId } = useOutletContext<ComisionContext>();
  return <TablaAtrasados comisionId={comisionId} />;
}
