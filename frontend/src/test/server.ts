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

export const STUB_LOTE_PENDIENTE = {
  lote_id: 'lote-1',
  tenant_id: 't-1',
  total: 5,
  pendientes: 5,
  enviando: 0,
  enviados: 0,
  errores: 0,
  cancelados: 0,
  asunto: 'Recordatorio de evaluación',
  cuerpo: 'Te informamos que tienes evaluaciones pendientes.',
  solicitado_por_nombre: 'Carlos López',
  destinatarios: ['ana@test.com', 'pedro@test.com', 'juan@test.com'],
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

  // C-24: liquidaciones
  http.get('http://localhost:8000/api/liquidaciones', () =>
    HttpResponse.json({ periodo: '2024-06', cohorte_id: 'k-1', mes: '2024-06', estado: 'Abierta', total_sin_factura: 500000, universo_facturante: 10, segmentos: [{ segmento: 'general', titulo: 'General', docentes: [{ usuario_id: 'u-1', nombre: 'Carlos López', rol: 'PLANTA', comisiones: ['Matemáticas 2024'], salario_base: 100000, salario_plus: 50000, total: 150000 }], total_segmento: 150000 }, { segmento: 'nexo', titulo: 'NEXO', docentes: [], total_segmento: 0 }, { segmento: 'factura', titulo: 'Con Factura', docentes: [{ usuario_id: 'u-2', nombre: 'María Pérez', rol: 'FACTURA', comisiones: ['Física 2024'], salario_base: 120000, salario_plus: 80000, total: 200000 }], total_segmento: 200000 }] }),
  ),
  http.post('http://localhost:8000/api/liquidaciones/cerrar', () =>
    HttpResponse.json({ periodo: '2024-06', estado: 'Cerrada', cerrada_at: '2024-07-01T00:00:00Z' }, { status: 201 }),
  ),
  http.get('http://localhost:8000/api/liquidaciones/historial', () =>
    HttpResponse.json([{ id: 'h-1', periodo: '2024-06', fecha_cierre: '2024-07-01T00:00:00Z', total_general: 350000, total_sin_factura: 150000, total_con_factura: 200000, estado: 'Cerrada' as const }]),
  ),
  http.get('http://localhost:8000/api/liquidaciones/historial/:id', () =>
    HttpResponse.json({ periodo: '2024-06', cohorte_id: 'k-1', mes: '2024-06', estado: 'Cerrada', total_sin_factura: 150000, universo_facturante: 5, segmentos: [{ segmento: 'general', titulo: 'General', docentes: [{ usuario_id: 'u-1', nombre: 'Carlos López', rol: 'PLANTA', comisiones: ['Matemáticas 2024'], salario_base: 100000, salario_plus: 50000, total: 150000 }], total_segmento: 150000 }] }),
  ),
  http.get('http://localhost:8000/api/liquidaciones/salarios-base', () =>
    HttpResponse.json([{ id: 'sb-1', rol: 'PLANTA', importe: 100000, vigencia_desde: '2024-03-01', vigencia_hasta: null, created_at: '', updated_at: '' }]),
  ),
  http.post('http://localhost:8000/api/liquidaciones/salarios-base', () =>
    HttpResponse.json({ id: 'sb-2', rol: 'NEXO', importe: 80000, vigencia_desde: '2024-03-01', vigencia_hasta: null, created_at: '', updated_at: '' }, { status: 201 }),
  ),
  http.patch('http://localhost:8000/api/liquidaciones/salarios-base/:id', () =>
    HttpResponse.json({ id: 'sb-1', rol: 'PLANTA', importe: 110000, vigencia_desde: '2024-03-01', vigencia_hasta: null, created_at: '', updated_at: '' }),
  ),
  http.delete('http://localhost:8000/api/liquidaciones/salarios-base/:id', () =>
    HttpResponse.json(null, { status: 204 }),
  ),
  http.get('http://localhost:8000/api/liquidaciones/salarios-plus', () =>
    HttpResponse.json([{ id: 'sp-1', clave: 'PLUS-ACT', rol: 'PLANTA', descripcion: 'Plus actividad', importe: 5000, vigencia_desde: '2024-03-01', vigencia_hasta: null, created_at: '', updated_at: '' }]),
  ),
  http.post('http://localhost:8000/api/liquidaciones/salarios-plus', () =>
    HttpResponse.json({ id: 'sp-2', clave: 'PLUS-DED', rol: 'NEXO', descripcion: 'Plus dedicación', importe: 6000, vigencia_desde: '2024-03-01', vigencia_hasta: null, created_at: '', updated_at: '' }, { status: 201 }),
  ),
  http.patch('http://localhost:8000/api/liquidaciones/salarios-plus/:id', () =>
    HttpResponse.json({ id: 'sp-1', clave: 'PLUS-ACT', rol: 'PLANTA', descripcion: 'Plus actividad', importe: 5500, vigencia_desde: '2024-03-01', vigencia_hasta: null, created_at: '', updated_at: '' }),
  ),
  http.delete('http://localhost:8000/api/liquidaciones/salarios-plus/:id', () =>
    HttpResponse.json(null, { status: 204 }),
  ),
  http.get('http://localhost:8000/api/facturas', () =>
    HttpResponse.json([{ id: 'f-1', fecha_carga: '2024-07-01T00:00:00Z', docente_id: 'u-2', docente_nombre: 'María Pérez', periodo: '2024-06', detalle: 'Factura junio 2024', estado: 'Pendiente', archivo_url: null, created_at: '', updated_at: '' }]),
  ),
  http.post('http://localhost:8000/api/facturas', () =>
    HttpResponse.json({ id: 'f-2', fecha_carga: '2024-07-02T00:00:00Z', docente_id: 'u-3', docente_nombre: 'Juan García', periodo: '2024-06', detalle: 'Factura junio 2024', estado: 'Pendiente', archivo_url: null, created_at: '', updated_at: '' }, { status: 201 }),
  ),
  http.patch('http://localhost:8000/api/facturas/:id', () =>
    HttpResponse.json({ id: 'f-1', fecha_carga: '2024-07-01T00:00:00Z', docente_id: 'u-2', docente_nombre: 'María Pérez', periodo: '2024-06', detalle: 'Factura junio 2024', estado: 'Abonada', archivo_url: null, created_at: '', updated_at: '' }),
  ),

  // C-24: admin / estructura
  http.get('http://localhost:8000/api/admin/carreras', () =>
    HttpResponse.json([{ id: 'car-1', codigo: 'LIC-MAT', nombre: 'Licenciatura en Matemática', estado: 'Activa' }]),
  ),
  http.post('http://localhost:8000/api/admin/carreras', () =>
    HttpResponse.json({ id: 'car-2', codigo: 'LIC-FIS', nombre: 'Licenciatura en Física', estado: 'Activa' }, { status: 201 }),
  ),
  http.put('http://localhost:8000/api/admin/carreras/:id', () =>
    HttpResponse.json({ id: 'car-1', codigo: 'LIC-MAT', nombre: 'Licenciatura en Matemática (actualizado)', estado: 'Activa' }),
  ),
  http.delete('http://localhost:8000/api/admin/carreras/:id', () =>
    HttpResponse.json(null, { status: 204 }),
  ),
  http.get('http://localhost:8000/api/admin/cohortes', () =>
    HttpResponse.json([{ id: 'coh-1', carrera_id: 'car-1', nombre: '2024', anio: 2024, vig_desde: '2024-03-01', vig_hasta: null, estado: 'Activo' }]),
  ),
  http.post('http://localhost:8000/api/admin/cohortes', () =>
    HttpResponse.json({ id: 'coh-2', carrera_id: 'car-1', nombre: '2025', anio: 2025, vig_desde: '2025-03-01', vig_hasta: null, estado: 'Activo' }, { status: 201 }),
  ),
  http.put('http://localhost:8000/api/admin/cohortes/:id', () =>
    HttpResponse.json({ id: 'coh-1', carrera_id: 'car-1', nombre: '2024 actualizado', anio: 2024, vig_desde: '2024-03-01', vig_hasta: null, estado: 'Activo' }),
  ),
  http.delete('http://localhost:8000/api/admin/cohortes/:id', () =>
    HttpResponse.json(null, { status: 204 }),
  ),
  http.get('http://localhost:8000/api/admin/materias', () =>
    HttpResponse.json([{ id: 'mat-1', codigo: 'MAT101', nombre: 'Álgebra', estado: 'Activa' }]),
  ),
  http.post('http://localhost:8000/api/admin/materias', () =>
    HttpResponse.json({ id: 'mat-2', codigo: 'FIS101', nombre: 'Física I', estado: 'Activa' }, { status: 201 }),
  ),
  http.put('http://localhost:8000/api/admin/materias/:id', () =>
    HttpResponse.json({ id: 'mat-1', codigo: 'MAT101', nombre: 'Álgebra (actualizado)', estado: 'Activa' }),
  ),
  http.delete('http://localhost:8000/api/admin/materias/:id', () =>
    HttpResponse.json(null, { status: 204 }),
  ),

  // C-24: admin / usuarios
  http.get('http://localhost:8000/api/admin/usuarios', () =>
    HttpResponse.json([{ id: 'usr-1', nombre: 'Admin', apellidos: 'Sistema', email: 'admin@trace.com', dni: '12345678', cuil: '20-12345678-9', roles: ['ADMIN'], estado: 'Activo', created_at: '', updated_at: '' }]),
  ),
  http.post('http://localhost:8000/api/admin/usuarios', () =>
    HttpResponse.json({ id: 'usr-2', nombre: 'Nuevo', apellidos: 'Usuario', email: 'nuevo@trace.com', dni: '87654321', cuil: '20-87654321-9', roles: ['PROFESOR'], estado: 'Activo', created_at: '', updated_at: '' }, { status: 201 }),
  ),
  http.put('http://localhost:8000/api/admin/usuarios/:id', () =>
    HttpResponse.json({ id: 'usr-1', nombre: 'Admin', apellidos: 'Sistema', email: 'admin@trace.com', dni: '12345678', cuil: '20-12345678-9', roles: ['ADMIN'], estado: 'Activo', created_at: '', updated_at: '' }),
  ),
  http.delete('http://localhost:8000/api/admin/usuarios/:id', () =>
    HttpResponse.json(null, { status: 204 }),
  ),

  // C-24: admin / auditoría
  http.get('http://localhost:8000/api/audit/metrics/actions-per-day', () =>
    HttpResponse.json([{ fecha: '2024-07-01', acciones: 150 }, { fecha: '2024-07-02', acciones: 200 }]),
  ),
  http.get('http://localhost:8000/api/audit/metrics/comunicacion-status', () =>
    HttpResponse.json([{ materia: 'Matemáticas', docente: 'Carlos López', pendientes: 5, enviando: 2, ok: 10, fallidos: 1, cancelados: 0 }]),
  ),
  http.get('http://localhost:8000/api/audit/metrics/interactions', () =>
    HttpResponse.json([]),
  ),
  http.get('http://localhost:8000/api/audit/metrics/last-actions', () =>
    HttpResponse.json([]),
  ),
  http.get('http://localhost:8000/api/audit/log', () =>
    HttpResponse.json({ total: 1, limit: 50, offset: 0, entries: [{ id: 'log-1', fecha_hora: '2024-07-01T10:00:00Z', usuario: 'admin@trace.com', usuario_id: 'usr-1', materia: 'Matemáticas', materia_id: 'mat-1', accion: 'Importar calificaciones', filas_afectadas: 30, ip: '127.0.0.1', user_agent: 'Mozilla/5.0' }] }),
  ),

  // C-12: comunicaciones
  http.post('http://localhost:8000/api/comunicaciones/preview', () =>
    HttpResponse.json({ asunto: 'Recordatorio', cuerpo: 'Tienes actividades pendientes.', destinatario: 'ana@test.com' }),
  ),
  http.post('http://localhost:8000/api/comunicaciones', () =>
    HttpResponse.json(STUB_COMUNICACIONES, { status: 201 }),
  ),
  http.get('http://localhost:8000/api/comunicaciones/lotes', () =>
    HttpResponse.json([STUB_LOTE_PENDIENTE]),
  ),
  http.get('http://localhost:8000/api/comunicaciones/lotes/:loteId', () =>
    HttpResponse.json(STUB_LOTE_STATUS),
  ),
  http.post('http://localhost:8000/api/comunicaciones/lotes/:loteId/aprobar', () =>
    HttpResponse.json(null, { status: 200 }),
  ),
  http.post('http://localhost:8000/api/comunicaciones/lotes/:loteId/rechazar', () =>
    HttpResponse.json(null, { status: 200 }),
  ),

  // C-23: equipos
  http.get('http://localhost:8000/api/equipos/mis-equipos', () =>
    HttpResponse.json([
      { id: 'eq-1', materia_nombre: 'Matemáticas', carrera: 'Lic. Matemática', cohorte: '2024', docente_nombre: 'Carlos López', rol: 'TITULAR', estado: 'Activo', vigencia_desde: '2024-03-01', vigencia_hasta: null },
      { id: 'eq-2', materia_nombre: 'Física', carrera: 'Lic. Física', cohorte: '2024', docente_nombre: 'María Pérez', rol: 'ADJUNTO', estado: 'Activo', vigencia_desde: '2024-03-01', vigencia_hasta: '2024-12-31' },
    ]),
  ),
  http.post('http://localhost:8000/api/equipos/asignacion-masiva', () =>
    HttpResponse.json({ creadas: 3 }, { status: 201 }),
  ),
  http.post('http://localhost:8000/api/equipos/clonar', () =>
    HttpResponse.json({ asignaciones: [{ id: 'eq-3', materia_nombre: 'Química', carrera: 'Lic. Química', cohorte: '2025', docente_nombre: 'Ana García', rol: 'TITULAR', estado: 'Activo', vigencia_desde: '2025-03-01', vigencia_hasta: null }] }, { status: 201 }),
  ),
  http.patch('http://localhost:8000/api/equipos/vigencia', () =>
    HttpResponse.json({ actualizadas: 2 }),
  ),

  // C-23: avisos
  http.get('http://localhost:8000/api/avisos', () =>
    HttpResponse.json([
      { id: 'av-1', titulo: 'Bienvenida', cuerpo: 'Bienvenidos al ciclo lectivo', alcance: 'Global', contexto_id: null, roles_destinatarios: [], severidad: 'Informativo', vigencia_desde: '2024-03-01', vigencia_hasta: '2024-12-31', orden_prioridad: 1, estado: 'activo', requiere_ack: false, created_at: '2024-03-01T00:00:00Z', updated_at: '2024-03-01T00:00:00Z' },
      { id: 'av-2', titulo: 'Recordatorio', cuerpo: 'Recordatorio entrega TP', alcance: 'PorMateria', contexto_id: 'm-1', roles_destinatarios: [], severidad: 'Advertencia', vigencia_desde: '2024-04-01', vigencia_hasta: '2024-04-30', orden_prioridad: 2, estado: 'activo', requiere_ack: true, created_at: '2024-04-01T00:00:00Z', updated_at: '2024-04-01T00:00:00Z' },
    ]),
  ),
  http.post('http://localhost:8000/api/avisos', () =>
    HttpResponse.json({ id: 'av-3', titulo: 'Nuevo aviso', cuerpo: 'Cuerpo del aviso', alcance: 'Global', contexto_id: null, roles_destinatarios: [], severidad: 'Informativo', vigencia_desde: '2024-03-01', vigencia_hasta: '2024-12-31', orden_prioridad: 1, estado: 'activo', requiere_ack: false, created_at: '2024-03-01T00:00:00Z', updated_at: '2024-03-01T00:00:00Z' }, { status: 201 }),
  ),
  http.put('http://localhost:8000/api/avisos/:id', () =>
    HttpResponse.json({ id: 'av-1', titulo: 'Bienvenida editada', cuerpo: 'Contenido editado', alcance: 'Global', contexto_id: null, roles_destinatarios: [], severidad: 'Urgente', vigencia_desde: '2024-03-01', vigencia_hasta: '2024-12-31', orden_prioridad: 1, estado: 'activo', requiere_ack: true, created_at: '2024-03-01T00:00:00Z', updated_at: '2024-04-01T00:00:00Z' }),
  ),
  http.delete('http://localhost:8000/api/avisos/:id', () =>
    HttpResponse.json(null, { status: 204 }),
  ),

  // C-23: tareas
  http.get('http://localhost:8000/api/tareas', () =>
    HttpResponse.json([
      { id: 'tr-1', titulo: 'Revisar planificaciones', descripcion: 'Revisar planificaciones del cuatrimestre', estado: 'Pendiente', materia_id: 'm-1', materia_nombre: 'Matemáticas', docente_asignado_nombre: 'Carlos López', docente_asignado_id: 'u-1', docente_asignador_nombre: 'Admin', docente_asignador_id: 'usr-1', created_at: '2024-03-01T00:00:00Z', updated_at: '2024-03-01T00:00:00Z' },
      { id: 'tr-2', titulo: 'Cargar actas', descripcion: 'Cargar actas de examen final', estado: 'EnProgreso', materia_id: 'm-2', materia_nombre: 'Física', docente_asignado_nombre: 'María Pérez', docente_asignado_id: 'u-2', docente_asignador_nombre: 'Admin', docente_asignador_id: 'usr-1', created_at: '2024-03-15T00:00:00Z', updated_at: '2024-03-16T00:00:00Z' },
    ]),
  ),
  http.patch('http://localhost:8000/api/tareas/:id/estado', () =>
    HttpResponse.json({ id: 'tr-1', titulo: 'Revisar planificaciones', descripcion: 'Revisar planificaciones del cuatrimestre', estado: 'EnProgreso', materia_id: 'm-1', materia_nombre: 'Matemáticas', docente_asignado_nombre: 'Carlos López', docente_asignado_id: 'u-1', docente_asignador_nombre: 'Admin', docente_asignador_id: 'usr-1', created_at: '2024-03-01T00:00:00Z', updated_at: '2024-03-02T00:00:00Z' }),
  ),
  http.get('http://localhost:8000/api/tareas/:id/comentarios', () =>
    HttpResponse.json([
      { id: 'cm-1', tarea_id: 'tr-1', autor_id: 'u-1', autor_nombre: 'Carlos López', texto: 'Comencé la revisión', created_at: '2024-03-02T00:00:00Z' },
      { id: 'cm-2', tarea_id: 'tr-1', autor_id: 'usr-1', autor_nombre: 'Admin', texto: 'Gracias, avísame cuando termines', created_at: '2024-03-02T00:00:00Z' },
    ]),
  ),
  http.post('http://localhost:8000/api/tareas/:id/comentarios', () =>
    HttpResponse.json({ id: 'cm-3', tarea_id: 'tr-1', autor_id: 'u-1', autor_nombre: 'Carlos López', texto: 'Nuevo comentario', created_at: '2024-03-03T00:00:00Z' }, { status: 201 }),
  ),
  http.post('http://localhost:8000/api/tareas/:id/delegar', () =>
    HttpResponse.json({ id: 'tr-1', titulo: 'Revisar planificaciones', descripcion: 'Revisar planificaciones del cuatrimestre', estado: 'Pendiente', materia_id: 'm-1', materia_nombre: 'Matemáticas', docente_asignado_nombre: 'Ana García', docente_asignado_id: 'u-3', docente_asignador_nombre: 'Admin', docente_asignador_id: 'usr-1', created_at: '2024-03-01T00:00:00Z', updated_at: '2024-03-02T00:00:00Z' }),
  ),

  // C-23: encuentros
  http.get('http://localhost:8000/api/encuentros', () =>
    HttpResponse.json([
      { id: 'en-1', materia_id: 'm-1', materia_nombre: 'Matemáticas', docente_id: 'u-1', docente_nombre: 'Carlos López', dia: 'Lunes', horario: '18:00 — 20:00', enlace: '', estado: 'Pendiente', grabacion: '' },
      { id: 'en-2', materia_id: 'm-2', materia_nombre: 'Física', docente_id: 'u-2', docente_nombre: 'María Pérez', dia: 'Miércoles', horario: '08:00 — 12:00', enlace: '', estado: 'Realizada', grabacion: '' },
    ]),
  ),
  http.get('http://localhost:8000/api/encuentros/slots', () =>
    HttpResponse.json([
      { id: 'sl-1', materia_id: 'm-1', materia_nombre: 'Matemáticas', dia: 'Lunes', horario: '18:00 — 20:00', fecha_inicio: '2024-03-01', cantidad_semanas: 16, titulo: 'Teórica', enlace: '' },
      { id: 'sl-2', materia_id: 'm-2', materia_nombre: 'Física', dia: 'Miércoles', horario: '08:00 — 12:00', fecha_inicio: '2024-03-01', cantidad_semanas: 16, titulo: 'Laboratorio', enlace: '' },
    ]),
  ),
  http.get('http://localhost:8000/api/guardias', () =>
    HttpResponse.json([
      { id: 'gu-1', tutor_id: 'u-1', tutor_nombre: 'Carlos López', materia_id: 'm-1', materia_nombre: 'Matemáticas', dia: 'Lunes', horario: '18:00 — 20:00', estado: 'Pendiente', comentarios: '' },
      { id: 'gu-2', tutor_id: 'u-2', tutor_nombre: 'María Pérez', materia_id: 'm-2', materia_nombre: 'Física', dia: 'Miércoles', horario: '08:00 — 12:00', estado: 'Confirmada', comentarios: '' },
    ]),
  ),

  // C-23: coloquios
  http.get('http://localhost:8000/api/coloquios/metricas', () =>
    HttpResponse.json({ total_alumnos: 150, instancias_activas: 5, reservas_activas: 45, notas_registradas: 230 }),
  ),
  http.get('http://localhost:8000/api/coloquios/convocatorias', () =>
    HttpResponse.json([
      { id: 'co-1', materia_id: 'm-1', materia_nombre: 'Matemáticas', instancia: '1er Parcial', dias_disponibles: ['2024-06-10', '2024-06-12'], cupos: 30, cupos_libres: 12, convocados: 18, reservas_activas: 15, estado: 'activa', created_at: '2024-06-01T00:00:00Z' },
      { id: 'co-2', materia_id: 'm-2', materia_nombre: 'Física', instancia: '2do Parcial', dias_disponibles: ['2024-06-15'], cupos: 25, cupos_libres: 25, convocados: 0, reservas_activas: 0, estado: 'cancelada', created_at: '2024-06-01T00:00:00Z' },
    ]),
  ),
  http.post('http://localhost:8000/api/coloquios/convocatorias', () =>
    HttpResponse.json({ id: 'co-3', materia_id: 'm-3', materia_nombre: 'Química', instancia: '1er Parcial', dias_disponibles: ['2024-07-01'], cupos: 20, cupos_libres: 20, convocados: 0, reservas_activas: 0, estado: 'activa', created_at: '2024-06-15T00:00:00Z' }, { status: 201 }),
  ),
  http.get('http://localhost:8000/api/coloquios/reservas', () =>
    HttpResponse.json([
      { id: 're-1', convocatoria_id: 'co-1', alumno_id: 'u-10', alumno_nombre: 'Pedro Gómez', dia: '2024-06-10', hora: '10:00', estado: 'activa' },
      { id: 're-2', convocatoria_id: 'co-1', alumno_id: 'u-11', alumno_nombre: 'Ana López', dia: '2024-06-12', hora: '14:00', estado: 'activa' },
    ]),
  ),
];

export const server = setupServer(...handlers);

// Re-export helpers for convenience in tests
export { http, HttpResponse };
