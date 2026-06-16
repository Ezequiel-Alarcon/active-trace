import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

// ─── Default stub data ────────────────────────────────────────────────────────

export const STUB_COMISIONES = [
  {
    id: 'c-1',
    materia_id: 'm-1',
    materia_nombre: 'Matemáticas',
    cohorte_id: 'k-1',
    cohorte_nombre: '2024',
  },
];

export const STUB_PREVIEW: CalificacionPreviewResponseStub = {
  preview_token: 'tok-abc',
  rows: [
    { usuario_id: 'u-1', materia_id: 'm-1', asignacion_id: 'a-1', nota: 8, valid: true, warnings: [] },
  ],
  total: 1,
  filename: 'notas.csv',
};

export const STUB_ATRASADOS = {
  total: 1,
  limit: 50,
  offset: 0,
  alumnos: [
    {
      usuario_id: 'u-2',
      email: 'ana@test.com',
      nombre: 'Ana García',
      materia_id: 'm-1',
      materia_nombre: 'Matemáticas',
      asignacion_id: 'a-1',
      asignacion_nombre: 'TP1',
      estado: 'Atrasado',
      nota_actual: null,
      umbral_pct: 60,
    },
  ],
};

export const STUB_RANKING = {
  materia_id: 'm-1',
  materia_nombre: 'Matemáticas',
  rankings: [
    { posicion: 1, usuario_id: 'u-1', nombre: 'Pedro', email: 'pedro@test.com', cantidad_aprobadas: 5, cantidad_totales: 6, nota_promedio: 8.5 },
  ],
};

export const STUB_NOTAS_FINALES = {
  total: 1,
  limit: 50,
  offset: 0,
  notas: [
    { materia_id: 'm-1', materia_nombre: 'Matemáticas', total_alumnos: 20, aprobados: 15, tasa_aprobacion: 0.75, nota_promedio_global: 7.2 },
  ],
};

export const STUB_REPORTE = {
  materia_id: 'm-1',
  materia_nombre: 'Matemáticas',
  cohorte_id: 'k-1',
  cohorte_nombre: '2024',
  total_alumnos: 20,
  alumnos: [],
};

export const STUB_TPS_SIN_CORREGIR = {
  total: 1,
  alumnos: [
    { usuario_id: 'u-1', materia_id: 'm-1', materia_nombre: 'Matemáticas' },
  ],
};

export const STUB_COMUNICACIONES: ComunicacionResponseStub[] = [
  {
    id: 'msg-1',
    tenant_id: 't-1',
    asunto: 'Recordatorio',
    cuerpo: 'Tienes actividades pendientes.',
    destinatario: 'ana@test.com',
    estado: 'Pendiente',
    lote_id: 'lote-1',
    error_detail: null,
    enviado_at: null,
    retry_count: 0,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

export const STUB_LOTE_STATUS = {
  lote_id: 'lote-1',
  tenant_id: 't-1',
  total: 1,
  pendientes: 1,
  enviando: 0,
  enviados: 0,
  errores: 0,
  cancelados: 0,
};

export const STUB_MONITOR = {
  datos: [
    { usuario_id: 'u-1', nombre: 'Pedro', email: 'pedro@test.com', comision: 'Matemáticas 2024' },
  ],
};

// ─── Stub types (mirrors backend shapes) ──────────────────────────────────────

interface CalificacionPreviewResponseStub {
  preview_token: string;
  rows: object[];
  total: number;
  filename: string;
}

interface ComunicacionResponseStub {
  id: string;
  tenant_id: string;
  asunto: string;
  cuerpo: string;
  destinatario: string;
  estado: string;
  lote_id: string | null;
  error_detail: string | null;
  enviado_at: string | null;
  retry_count: number;
  created_at: string;
  updated_at: string;
}

// ─── Initial handlers ─────────────────────────────────────────────────────────
// Default: refresh returns 401 (no active session) — prevents AggregateError noise
// Individual tests override these via server.use(...)
export const handlers = [
  http.post('http://localhost:8000/api/auth/refresh', () =>
    HttpResponse.json({ code: 'AUTH_TOKEN_EXPIRED' }, { status: 401 }),
  ),

  // C-10: calificaciones
  http.get('http://localhost:8000/api/calificaciones', () =>
    HttpResponse.json([]),
  ),
  http.post('http://localhost:8000/api/calificaciones/import/preview', () =>
    HttpResponse.json(STUB_PREVIEW),
  ),
  http.post('http://localhost:8000/api/calificaciones/import/confirm', () =>
    HttpResponse.json({ persisted: 1, skipped: 0, failed: 0 }),
  ),

  // C-10: umbral-materia
  http.get('http://localhost:8000/api/umbral-materia', () =>
    HttpResponse.json([]),
  ),
  http.post('http://localhost:8000/api/umbral-materia', () =>
    HttpResponse.json({ id: 'u-1', materia_id: 'm-1', asignacion_id: null, umbral_pct: 60, created_at: '', updated_at: '' }, { status: 201 }),
  ),

  // C-11: analisis
  http.get('http://localhost:8000/api/analisis/atrasados', () =>
    HttpResponse.json(STUB_ATRASADOS),
  ),
  http.get('http://localhost:8000/api/analisis/ranking', () =>
    HttpResponse.json(STUB_RANKING),
  ),
  http.get('http://localhost:8000/api/reportes/notas-finales', () =>
    HttpResponse.json(STUB_NOTAS_FINALES),
  ),
  http.get('http://localhost:8000/api/reportes/materia/:materiaId', () =>
    HttpResponse.json(STUB_REPORTE),
  ),
  http.get('http://localhost:8000/api/exportacion/tps-sin-corregir', () =>
    HttpResponse.json(STUB_TPS_SIN_CORREGIR),
  ),
  http.get('http://localhost:8000/api/monitores/seguimiento', () =>
    HttpResponse.json(STUB_MONITOR),
  ),
  http.get('http://localhost:8000/api/monitores/general', () =>
    HttpResponse.json(STUB_MONITOR),
  ),

  // C-12: comunicaciones
  http.post('http://localhost:8000/api/comunicaciones/preview', () =>
    HttpResponse.json({ asunto: 'Recordatorio', cuerpo: 'Tienes actividades pendientes.', destinatario: 'ana@test.com' }),
  ),
  http.post('http://localhost:8000/api/comunicaciones', () =>
    HttpResponse.json(STUB_COMUNICACIONES, { status: 201 }),
  ),
  http.get('http://localhost:8000/api/comunicaciones/lotes/:loteId', () =>
    HttpResponse.json(STUB_LOTE_STATUS),
  ),
];

export const server = setupServer(...handlers);

// Re-export helpers for convenience in tests
export { http, HttpResponse };
