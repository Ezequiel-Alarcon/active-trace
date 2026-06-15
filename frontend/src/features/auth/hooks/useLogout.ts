import { useNavigate } from 'react-router-dom';
import { useAuth } from '../components/AuthProvider';
import { logout as logoutApi } from '../services/authApi';

export function useLogout() {
  const navigate = useNavigate();
  const { clearSession } = useAuth();

  return async function doLogout() {
    try {
      await logoutApi();
    } catch {
      // Best-effort revocation — always clear locally even if backend errors
    } finally {
      clearSession();
      navigate('/login', { replace: true });
    }
  };
}
