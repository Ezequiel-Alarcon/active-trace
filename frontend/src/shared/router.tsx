import { createBrowserRouter } from 'react-router-dom';
import RequireAuth from './components/RequireAuth';
import RequirePermission from './components/RequirePermission';
import AppLayout from './components/AppLayout';
import NotFound404 from './components/NotFound404';
import LoginPage from '@/features/auth/pages/LoginPage';
import ForgotPasswordPage from '@/features/auth/pages/ForgotPasswordPage';
import ResetPasswordPage from '@/features/auth/pages/ResetPasswordPage';
import ComisionPage from '@/features/comision/pages/ComisionPage';
import ImportarCalificacionesPage from '@/features/calificaciones/pages/ImportarCalificacionesPage';
import AtrasadosPage from '@/features/analisis/pages/AtrasadosPage';
import RankingPage from '@/features/analisis/pages/RankingPage';
import NotasFinalesPage from '@/features/analisis/pages/NotasFinalesPage';
import ReportesPage from '@/features/analisis/pages/ReportesPage';
import EntregasSinCorregirPage from '@/features/entregas/pages/EntregasSinCorregirPage';
import ComunicarPage from '@/features/comunicacion/pages/ComunicarPage';
import MonitorPage from '@/features/monitor/pages/MonitorPage';

// Placeholder dashboard page for the authenticated shell
function DashboardPage() {
  return (
    <div className="flex flex-col gap-2">
      <h1 className="text-2xl font-semibold text-gray-800">Inicio</h1>
      <p className="text-gray-600">Bienvenido a Active Trace.</p>
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

          // ── C-22: comisión workspace ──────────────────────────────────────
          {
            path: '/comision',
            element: (
              <RequirePermission permission="analisis:ver">
                <ComisionPage />
              </RequirePermission>
            ),
            children: [
              {
                path: 'importar',
                element: (
                  <RequirePermission permission="calificaciones:importar">
                    <ImportarCalificacionesPage />
                  </RequirePermission>
                ),
              },
              {
                path: 'atrasados',
                element: (
                  <RequirePermission permission="analisis:ver">
                    <AtrasadosPage />
                  </RequirePermission>
                ),
              },
              {
                path: 'ranking',
                element: (
                  <RequirePermission permission="analisis:ver">
                    <RankingPage />
                  </RequirePermission>
                ),
              },
              {
                path: 'notas-finales',
                element: (
                  <RequirePermission permission="analisis:ver">
                    <NotasFinalesPage />
                  </RequirePermission>
                ),
              },
              {
                path: 'reportes',
                element: (
                  <RequirePermission permission="analisis:ver">
                    <ReportesPage />
                  </RequirePermission>
                ),
              },
              {
                path: 'entregas',
                element: (
                  <RequirePermission permission="analisis:ver">
                    <EntregasSinCorregirPage />
                  </RequirePermission>
                ),
              },
              {
                path: 'comunicar',
                element: (
                  <RequirePermission permission="comunicacion:enviar">
                    <ComunicarPage />
                  </RequirePermission>
                ),
              },
            ],
          },

          // ── C-22: monitor de seguimiento (standalone) ─────────────────────
          {
            path: '/monitor',
            element: (
              <RequirePermission permission="analisis:ver">
                <MonitorPage />
              </RequirePermission>
            ),
          },

          {
            path: '*',
            element: <NotFound404 />,
          },
        ],
      },
    ],
  },
]);
