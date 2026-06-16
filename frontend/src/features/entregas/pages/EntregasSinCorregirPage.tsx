import { useOutletContext } from 'react-router-dom';
import EntregasSinCorregir from '../components/EntregasSinCorregir';

interface ComisionContext {
  comisionId: string;
}

export default function EntregasSinCorregirPage() {
  const { comisionId } = useOutletContext<ComisionContext>();
  return <EntregasSinCorregir comisionId={comisionId} />;
}
