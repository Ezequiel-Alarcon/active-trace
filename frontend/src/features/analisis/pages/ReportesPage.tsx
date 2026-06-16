import { useOutletContext } from 'react-router-dom';
import ReportesVista from '../components/ReportesVista';

interface ComisionContext {
  comisionId: string;
}

export default function ReportesPage() {
  const { comisionId } = useOutletContext<ComisionContext>();
  return <ReportesVista comisionId={comisionId} />;
}
