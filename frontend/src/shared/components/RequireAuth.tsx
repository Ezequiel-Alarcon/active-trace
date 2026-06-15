import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '@/features/auth/components/AuthProvider';

/**
 * Route wrapper that redirects unauthenticated users to /login.
 * While the session bootstrap is in flight, renders a loading state
 * to avoid premature redirects (spec: bootstrap-in-progress shows loading).
 */
export default function RequireAuth() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="flex items-center justify-center min-h-screen"
      >
        <span className="sr-only">Cargando sesión…</span>
        <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
