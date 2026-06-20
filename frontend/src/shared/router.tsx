import { createBrowserRouter, Navigate } from 'react-router-dom';
import { lazy } from 'react';
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
import AprobacionesPage from '@/features/comunicacion/pages/AprobacionesPage';
import ComunicarPage from '@/features/comunicacion/pages/ComunicarPage';
import MonitorPage from '@/features/monitor/pages/MonitorPage';

// ── Alumno pages (lazy-loaded) ────────────────────────────────────────────
const MiAcademiaPage = lazy(() => import('@/features/alumno/pages/MiAcademiaPage'));
const MisReservasPage = lazy(() => import('@/features/alumno/pages/MisReservasPage'));

// ── Profesor pages (lazy-loaded) ──────────────────────────────────────────
const GuardiasPage = lazy(() => import('@/features/guardias/pages/GuardiasPage'));
const MensajesPage = lazy(() => import('@/features/mensajes/pages/MensajesPage'));
const PerfilPage = lazy(() => import('@/features/perfil/pages/PerfilPage'));
const MisEquiposProfesorPage = lazy(() => import('@/features/equipos/pages/MisEquiposProfesorPage'));

// ── Coordinación pages (lazy-loaded) ──────────────────────────────────────
const EquiposPage = lazy(() => import('@/features/equipos/pages/EquiposPage'));
const AvisosPage = lazy(() => import('@/features/avisos/pages/AvisosPage'));
const TareasPage = lazy(() => import('@/features/tareas/pages/TareasPage'));
const MonitorGeneralPage = lazy(() => import('@/features/monitor/pages/MonitorGeneralPage'));
const EncuentrosPage = lazy(() => import('@/features/encuentros/pages/EncuentrosPage'));
const ColoquiosPage = lazy(() => import('@/features/coloquios/pages/ColoquiosPage'));
const SetupPage = lazy(() => import('@/features/setup-cuatrimestre/pages/SetupPage'));

// ── C-24: Administración pages (lazy-loaded) ───────────────────────────────
const LiquidacionPeriodoPage = lazy(() => import('@/features/liquidaciones/pages/LiquidacionPeriodoPage'));
const HistorialPage = lazy(() => import('@/features/liquidaciones/pages/HistorialPage'));
const GrillaSalarialPage = lazy(() => import('@/features/liquidaciones/pages/GrillaSalarialPage'));
const FacturasPage = lazy(() => import('@/features/liquidaciones/pages/FacturasPage'));
const EstructuraPage = lazy(() => import('@/features/admin/pages/EstructuraPage'));
const UsuariosPage = lazy(() => import('@/features/admin/pages/UsuariosPage'));
const AuditoriaPanelPage = lazy(() => import('@/features/admin/pages/AuditoriaPanelPage'));
const AuditoriaLogPage = lazy(() => import('@/features/admin/pages/AuditoriaLogPage'));

const DashboardPage = lazy(() => import('@/features/dashboard/pages/DashboardPage'));

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
            element: <DashboardPage />,
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
              {
                path: 'aprobaciones',
                element: (
                  <RequirePermission permission="comunicacion:aprobar">
                    <AprobacionesPage />
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

          // ── C-24: liquidaciones (sección agrupada) ──────────────────────────
          {
            path: '/admin/liquidaciones',
            element: <Navigate to="/admin/liquidaciones/periodo" replace />,
          },
          {
            path: '/admin/liquidaciones/periodo',
            element: (
              <RequirePermission permission="liquidaciones:ver">
                <LiquidacionPeriodoPage />
              </RequirePermission>
            ),
          },
          {
            path: '/admin/liquidaciones/historial',
            element: (
              <RequirePermission permission="liquidaciones:ver">
                <HistorialPage />
              </RequirePermission>
            ),
          },
          {
            path: '/admin/liquidaciones/grilla',
            element: (
              <RequirePermission permission="liquidaciones:configurar-salarios">
                <GrillaSalarialPage />
              </RequirePermission>
            ),
          },
          {
            path: '/admin/liquidaciones/facturas',
            element: (
              <RequirePermission permission="liquidaciones:ver">
                <FacturasPage />
              </RequirePermission>
            ),
          },

          // ── C-24: administración (sección agrupada) ──────────────────────────
          {
            path: '/admin',
            element: <Navigate to="/admin/estructura" replace />,
          },
          {
            path: '/admin/estructura',
            element: (
              <RequirePermission permission="estructura:gestionar">
                <EstructuraPage />
              </RequirePermission>
            ),
          },
          {
            path: '/admin/usuarios',
            element: (
              <RequirePermission permission="usuarios:gestionar">
                <UsuariosPage />
              </RequirePermission>
            ),
          },
          {
            path: '/admin/auditoria',
            element: (
              <RequirePermission permission="auditoria:ver">
                <AuditoriaPanelPage />
              </RequirePermission>
            ),
          },
          {
            path: '/admin/auditoria/log',
            element: (
              <RequirePermission permission="auditoria:ver">
                <AuditoriaLogPage />
              </RequirePermission>
            ),
          },

          // ── C-23: coordinación (sección agrupada) ──────────────────────────
          {
            path: '/coordinacion',
            element: <Navigate to="/coordinacion/equipos" replace />,
          },
          {
            path: '/coordinacion/equipos',
            element: (
              <RequirePermission permission="equipos:asignar">
                <EquiposPage />
              </RequirePermission>
            ),
          },
          {
            path: '/coordinacion/avisos',
            element: (
              <RequirePermission permission="avisos:publicar">
                <AvisosPage />
              </RequirePermission>
            ),
          },
          {
            path: '/coordinacion/tareas',
            element: (
              <RequirePermission permission="tareas:gestionar">
                <TareasPage />
              </RequirePermission>
            ),
          },
          {
            path: '/coordinacion/monitor',
            element: (
              <RequirePermission permission="equipos:asignar">
                <MonitorGeneralPage />
              </RequirePermission>
            ),
          },
          {
            path: '/coordinacion/encuentros',
            element: (
              <RequirePermission permission="encuentros:gestionar">
                <EncuentrosPage />
              </RequirePermission>
            ),
          },
          {
            path: '/coordinacion/coloquios',
            element: (
              <RequirePermission permission="coloquios:ver">
                <ColoquiosPage />
              </RequirePermission>
            ),
          },
          {
            path: '/coordinacion/setup',
            element: (
              <RequirePermission permission="estructura:gestionar">
                <SetupPage />
              </RequirePermission>
            ),
          },

          // ── Profesor ──────────────────────────────────────────────────────
          {
            path: '/profesor/guardias',
            element: (
              <RequirePermission permission="encuentros:registrar_guardia">
                <GuardiasPage />
              </RequirePermission>
            ),
          },
          {
            path: '/profesor/mensajes',
            element: (
              <RequirePermission permission="mensajes:ver">
                <MensajesPage />
              </RequirePermission>
            ),
          },
          {
            path: '/profesor/equipos',
            element: (
              <RequirePermission permission="equipos:ver">
                <MisEquiposProfesorPage />
              </RequirePermission>
            ),
          },

          // ── Alumno ──────────────────────────────────────────────────────
          {
            path: '/alumno/academia',
            element: (
              <RequirePermission permission="academico:ver_estado_propio">
                <MiAcademiaPage />
              </RequirePermission>
            ),
          },
          {
            path: '/alumno/reservas',
            element: (
              <RequirePermission permission="coloquios:reservar">
                <MisReservasPage />
              </RequirePermission>
            ),
          },

          // ── Perfil (todos los roles) ───────────────────────────────────
          {
            path: '/perfil',
            element: <PerfilPage />,
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
