import { createBrowserRouter } from 'react-router-dom';
import RequireAuth from './components/RequireAuth';
import RequirePermission from './components/RequirePermission';
import AppLayout from './components/AppLayout';
import NotFound404 from './components/NotFound404';
import LoginPage from '@/features/auth/pages/LoginPage';
import ForgotPasswordPage from '@/features/auth/pages/ForgotPasswordPage';
import ResetPasswordPage from '@/features/auth/pages/ResetPasswordPage';

// Placeholder dashboard page for the authenticated shell
function DashboardPage() {
  return (
    <div className="flex flex-col gap-2">
      <h1 className="text-2xl font-semibold text-gray-800">Inicio</h1>
      <p className="text-gray-600">Bienvenido a Active Trace.</p>
      {/* TODO: (FEAT) Replace with real dashboard content in C-22/C-23 */}
    </div>
  );
}

export const router = createBrowserRouter([
  // ── Public routes (outside AppLayout) ────────────────────────────────────
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/forgot',
    element: <ForgotPasswordPage />,
  },
  {
    path: '/reset',
    element: <ResetPasswordPage />,
  },

  // ── Protected routes (inside RequireAuth + AppLayout) ─────────────────────
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppLayout />,
        children: [
          {
            path: '/',
            element: (
              <RequirePermission permission="alumnos:ver">
                <DashboardPage />
              </RequirePermission>
            ),
          },
          // TODO: (FEAT) Add feature routes here as C-22/C-23/C-24 are implemented
          {
            path: '*',
            element: <NotFound404 />,
          },
        ],
      },
    ],
  },
]);
