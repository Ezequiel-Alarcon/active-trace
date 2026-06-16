import { useOutletContext } from 'react-router-dom';
import RankingVista from '../components/RankingVista';

interface ComisionContext {
  comisionId: string;
}

export default function RankingPage() {
  const { comisionId } = useOutletContext<ComisionContext>();
  return <RankingVista comisionId={comisionId} />;
}
