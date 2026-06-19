export type LiquidacionSegmento = 'general' | 'nexo' | 'factura';

export interface LiquidacionDocenteEntry {
  usuario_id: string;
  nombre: string;
  rol: string;
  comisiones: string[];
  salario_base: number;
  salario_plus: number;
  total: number;
}

export interface LiquidacionSegmentEntry {
  segmento: LiquidacionSegmento;
  titulo: string;
  docentes: LiquidacionDocenteEntry[];
}

export interface LiquidacionPeriodoResponse {
  periodo: string;
  cohorte_id: string;
  mes: string;
  estado: 'Abierta' | 'Cerrada';
  total_sin_factura: number;
  universo_facturante: number;
  segmentos: LiquidacionSegmentEntry[];
}

export interface SalarioBase {
  id: string;
  rol: string;
  importe: number;
  vigencia_desde: string;
  vigencia_hasta: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateSalarioBaseRequest {
  rol: string;
  importe: number;
  vigencia_desde: string;
  vigencia_hasta?: string | null;
}

export interface UpdateSalarioBaseRequest {
  importe?: number;
  vigencia_desde?: string;
  vigencia_hasta?: string | null;
}

export interface SalarioPlus {
  id: string;
  clave: string;
  rol: string;
  descripcion: string;
  importe: number;
  vigencia_desde: string;
  vigencia_hasta: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateSalarioPlusRequest {
  clave: string;
  rol: string;
  descripcion: string;
  importe: number;
  vigencia_desde: string;
  vigencia_hasta?: string | null;
}

export interface UpdateSalarioPlusRequest {
  descripcion?: string;
  importe?: number;
  vigencia_desde?: string;
  vigencia_hasta?: string | null;
}

export type FacturaEstado = 'Pendiente' | 'Abonada';

export interface Factura {
  id: string;
  fecha_carga: string;
  docente_id: string;
  docente_nombre: string;
  periodo: string;
  detalle: string;
  estado: FacturaEstado;
  archivo_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateFacturaRequest {
  docente_id: string;
  periodo: string;
  detalle: string;
  archivo_url?: string | null;
}

export interface LiquidacionHistorialEntry {
  id: string;
  periodo: string;
  fecha_cierre: string;
  total_general: number;
  total_sin_factura: number;
  total_con_factura: number;
  estado: 'Cerrada';
}

export interface LiquidacionCierreResponse {
  periodo: string;
  estado: 'Cerrada';
  cerrada_at: string;
}
