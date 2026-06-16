import { useOutletContext } from 'react-router-dom';
import ImportarCalificacionesForm from '../components/ImportarCalificacionesForm';

interface ComisionContext {
  comisionId: string;
}

/**
 * Page for importing calificaciones for a comision.
 * Receives comisionId from the ComisionPage outlet context.
 */
export default function ImportarCalificacionesPage() {
  const { comisionId } = useOutletContext<ComisionContext>();
  return <ImportarCalificacionesForm comisionId={comisionId} />;
}
